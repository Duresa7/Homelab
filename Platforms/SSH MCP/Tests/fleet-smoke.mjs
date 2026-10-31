#!/usr/bin/env node
// Fleet smoke test for ssh-mcp over Streamable HTTP, with no dependencies.
//
//   SSH_MCP_BEARER_TOKEN=... [PROFILES=a,b] node fleet-smoke.mjs <config.toml> [url]
//
// Lists the tools, then runs `whoami` on every profile through run-command and
// `id -u` through privileged-command on every Linux profile that does not log in as
// root. A profile passes when whoami prints its configured user and privileged
// id -u prints 0. Exit status is the number of failures.
import { readFileSync } from 'node:fs';

const [configPath, url = 'http://192.168.40.39:8813/'] = process.argv.slice(2);
const token = process.env.SSH_MCP_BEARER_TOKEN;
if (!configPath || !token) {
  console.error('usage: SSH_MCP_BEARER_TOKEN=... node fleet-smoke.mjs <config.toml> [url]');
  process.exit(64);
}

// Each profile block follows its own comment line, which marks Windows hosts.
const blocks = readFileSync(configPath, 'utf8').split('[[profiles]]');
const profiles = blocks.slice(1).map((block, i) => ({
  name: block.match(/^name = "([^"]+)"/m)[1],
  user: block.match(/^user = "([^"]+)"/m)[1],
  windows: blocks[i].trimEnd().split('\n').at(-1).includes('(Windows OpenSSH)'),
})).filter((p) => !process.env.PROFILES || process.env.PROFILES.split(',').includes(p.name));

let session;
let nextId = 1;
async function rpc(method, params, notify = false) {
  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
    Accept: 'application/json, text/event-stream',
  };
  if (session) headers['Mcp-Session-Id'] = session;
  const body = notify ? { jsonrpc: '2.0', method, params } : { jsonrpc: '2.0', id: nextId++, method, params };
  const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body) });
  session = res.headers.get('mcp-session-id') ?? session;
  if (notify) return null;
  const raw = await res.text();
  const payload = res.headers.get('content-type')?.includes('text/event-stream')
    ? raw.split('\n').filter((l) => l.startsWith('data:')).map((l) => JSON.parse(l.slice(5))).find((m) => m.id !== undefined)
    : JSON.parse(raw);
  if (!res.ok || payload.error) throw new Error(`${method}: HTTP ${res.status} ${JSON.stringify(payload.error ?? raw).slice(0, 300)}`);
  return payload.result;
}

const call = async (name, args) => {
  const result = await rpc('tools/call', { name, arguments: args });
  return { ok: !result.isError, text: result.content.map((c) => c.text ?? '').join('\n') };
};
const lastLine = (s) => s.trim().split('\n').filter(Boolean).at(-1)?.trim() ?? '';

await rpc('initialize', {
  protocolVersion: '2025-06-18',
  capabilities: {},
  clientInfo: { name: 'fleet-smoke', version: '1' },
});
await rpc('notifications/initialized', {}, true);
const { tools } = await rpc('tools/list', {});
console.log(`tools (${tools.length}): ${tools.map((t) => t.name).join(', ')}`);

async function check(p) {
  const row = { profile: p.name, whoami: '', privileged: '-', pass: true };
  try {
    const who = await call('run-command', { profile: p.name, command: 'whoami' });
    row.whoami = lastLine(who.text);
    row.pass = who.ok && row.whoami.toLowerCase().endsWith(p.user.toLowerCase());
    if (!who.ok) row.whoami = who.text.slice(0, 160);
    if (!p.windows && p.user !== 'root') {
      const priv = await call('privileged-command', { profile: p.name, command: 'id -u' });
      row.privileged = priv.ok ? lastLine(priv.text) : priv.text.slice(0, 160);
      row.pass &&= priv.ok && row.privileged.endsWith('0');
    }
  } catch (err) {
    row.pass = false;
    row.whoami = String(err.message).slice(0, 160);
  }
  return row;
}

const rows = [];
for (let i = 0; i < profiles.length; i += 6) {
  rows.push(...(await Promise.all(profiles.slice(i, i + 6).map(check))));
}
for (const r of rows) {
  console.log(`${r.pass ? 'PASS' : 'FAIL'}  ${r.profile.padEnd(20)} whoami=${r.whoami}  sudo-id=${r.privileged}`);
}
const failed = rows.filter((r) => !r.pass).length;
console.log(`${rows.length - failed}/${rows.length} profiles passed`);
process.exit(failed);
