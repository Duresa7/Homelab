// Executor 2 apps that wrap an MCP server behind a static bearer token. Each token lives
// in the password manager under `item` and reaches the deploy script as TOKEN_<SLUG>.
export const ORIGIN = 'https://executor.alphasecunited.com';
// framework.release on 2026-11-13 (Executor 2.0.0-beta.41). Bump with the image.
export const FRAMEWORK = '0.0.1-beta.122';
export const MCP_SDK = '1.32.1';

// Cloudflare left this list on 2026-11-01, when the `cloudflare` slug became the official
// catalog app with its own OAuth account. Deploying a bearer app to that slug would replace it.
export const APPS = [
  {
    slug: 'ssh',
    name: 'SSH',
    provider: 'ssh-mcp on docker-blue',
    url: 'http://192.168.40.39:8813/',
    host: '192.168.40.39:8813',
    // ssh-mcp stops a command at 240 s; this leaves room for its answer.
    timeoutMs: 280000,
    item: 'SSH MCP Bearer Token - docker-blue',
    field: 'credential',
  },
  {
    slug: 'unifi',
    name: 'UniFi',
    provider: 'UniFi MCP gateway on docker-blue',
    url: 'http://192.168.40.39:8811/mcp',
    host: '192.168.40.39:8811',
    timeoutMs: 120000,
    item: 'UniFi MCP Gateway Bearer Token - docker-blue',
    field: 'credential',
  },
  {
    slug: 'wazuh',
    name: 'Wazuh',
    provider: 'Wazuh MCP Server on security-01',
    url: 'http://192.168.72.2:3000/mcp',
    host: '192.168.72.2:3000',
    timeoutMs: 120000,
    item: 'Wazuh MCP Server credentials',
    field: 'MCP API key',
  },
];
