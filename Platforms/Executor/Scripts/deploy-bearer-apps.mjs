#!/usr/bin/env node
// Create, deploy and connect the Executor 2 apps that wrap a bearer-token MCP server.
//
//   EXECUTOR_PAT=... TOKEN_<SLUG>=... node deploy-bearer-apps.mjs [slug ...]
//
// EXECUTOR_PAT and one TOKEN_<SLUG> per app are injected from my password manager at run
// time, so no value is ever on a command line. Source and deploys go through Executor's MCP endpoint
// with the PAT. The bearer token goes straight to the connection's submit endpoint over
// HTTPS and never through an MCP call. Re-running redeploys the current source and
// connects only apps whose requirement has no account yet.
import { APPS, FRAMEWORK, MCP_SDK, ORIGIN } from './bearer-apps.config.mjs';

const pat = process.env.EXECUTOR_PAT;
if (!pat) throw new Error('EXECUTOR_PAT is not set');
const only = process.argv.slice(2);

const indexTs = (a) => `import { defineApp, defineProvider, object, router, secrets, string } from "apps";
import { mcpHealth, mcpRouter } from "apps/mcp";

const url = ${JSON.stringify(a.url)};
const headers = (account: { fields: { token: string } }) => ({
  Authorization: "Bearer " + account.fields.token,
});

// hosts keeps the token an opaque handle in app code; Executor substitutes the value only
// on requests to this host.
const server = defineProvider({
  name: ${JSON.stringify(a.provider)},
  hosts: [${JSON.stringify(a.host)}],
  auth: {
    bearer: secrets({
      label: "Bearer token",
      fields: object({ token: string({ minLength: 1 }) }),
    }),
  },
  health: (check) => mcpHealth(check, { url, headers: headers(check.account) }),
});

export default defineApp({ app: { accounts: { server } } }, async (ctx) => {
  const account = ctx.app?.accounts.server;
  if (!account) return { tools: router({}) };
  return {
    tools: await mcpRouter({
      url,
      account,
      headers: headers(account),
      timeoutMs: ${a.timeoutMs},
      signal: ctx.signal,
    }),
  };
});
`;

const packageJson = (a) => JSON.stringify({
  name: a.slug,
  private: true,
  type: 'module',
  dependencies: { apps: FRAMEWORK, '@modelcontextprotocol/sdk': MCP_SDK },
}, null, 2) + '\n';

let session;
let nextId = 1;
async function rpc(method, params, notify = false) {
  const headers = {
    Authorization: `Bearer ${pat}`,
    'Content-Type': 'application/json',
    Accept: 'application/json, text/event-stream',
  };
  if (session) headers['Mcp-Session-Id'] = session;
  const body = notify ? { jsonrpc: '2.0', method, params } : { jsonrpc: '2.0', id: nextId++, method, params };
  const res = await fetch(`${ORIGIN}/mcp`, { method: 'POST', headers, body: JSON.stringify(body) });
  session = res.headers.get('mcp-session-id') ?? session;
  if (notify) return null;
  const raw = await res.text();
  const msg = res.headers.get('content-type')?.includes('text/event-stream')
    ? raw.split('\n').filter((l) => l.startsWith('data:')).map((l) => JSON.parse(l.slice(5))).find((m) => m.id !== undefined)
    : JSON.parse(raw);
  if (msg.error) throw new Error(`${method}: ${JSON.stringify(msg.error)}`);
  return msg.result;
}

async function call(path, input) {
  const result = await rpc('tools/call', { name: 'call', arguments: { calls: { path, input } } });
  const text = result.content.map((c) => c.text ?? '').join('');
  const outer = JSON.parse(text);
  const inner = outer.execution?.value;
  if (!outer.execution?.ok || !inner?.ok) throw new Error(`${path}: ${text.slice(0, 600)}`);
  return inner.value;
}

await rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'deploy-bearer-apps', version: '1' } });
await rpc('notifications/initialized', {}, true);

const release = await call('tools.executor.framework.release', {});
if (release.version !== FRAMEWORK) throw new Error(`server runs apps ${release.version}; config pins ${FRAMEWORK}`);

const { organization } = await call('tools.executor.context.get', {});
const existing = new Map((await call('tools.executor.appManagement.list', {})).map((app) => [app.slug, app]));

for (const a of APPS.filter((x) => only.length === 0 || only.includes(x.slug))) {
  const files = [
    { path: 'index.ts', content: indexTs(a) },
    { path: 'package.json', content: packageJson(a) },
  ];
  let app = existing.get(a.slug);
  if (!app) app = await call('tools.executor.appManagement.create', { body: { name: a.name, files } });
  if (app.slug !== a.slug) throw new Error(`${a.name} got slug ${app.slug}, expected ${a.slug}`);
  const deployed = await call('tools.executor.appManagement.deploy', { path: { app: app.id }, body: { files } });
  console.log(`${a.slug}: app ${app.id} deployed ${deployed.version?.id ?? deployed.activeVersion ?? JSON.stringify(deployed).slice(0, 80)}`);

  const requirement = await call('tools.executor.appAccounts.appGet', { path: { app: app.id, requirement: 'server' } });
  if (requirement.accounts.some((entry) => entry.linked)) {
    console.log(`${a.slug}: account already linked`);
    continue;
  }
  const token = process.env[`TOKEN_${a.slug.toUpperCase()}`];
  if (!token) throw new Error(`TOKEN_${a.slug.toUpperCase()} is not set`);
  const connection = await call('tools.executor.appAccounts.appConnect', { path: { app: app.id, requirement: 'server' }, body: {} });
  const res = await fetch(`${ORIGIN}/api/organizations/${organization}/connections/${connection.id}/submit`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${pat}`, 'Content-Type': 'application/json', Origin: ORIGIN },
    body: JSON.stringify({ method: 'bearer', label: `${a.name} bearer token`, fields: { token } }),
  });
  const answer = await res.text();
  if (!res.ok) throw new Error(`${a.slug}: submit HTTP ${res.status} ${answer.slice(0, 300)}`);
  const account = JSON.parse(answer);
  console.log(`${a.slug}: connected account ${account.id} (${account.label})`);
}
