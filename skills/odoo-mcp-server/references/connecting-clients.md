# Connecting an MCP client to the Odoo `/mcp` endpoint

## Client quick-reference

| Client | How |
|---|---|
| Claude.ai / Desktop | Settings → Connectors → Add custom connector → `https://<odoo>/mcp` → log in + consent. |
| Claude Code | `claude mcp add --transport http much-odoo https://<odoo>/mcp`, then `/mcp` → Authenticate. |
| ChatGPT | Developer mode → Settings → Apps & Connectors → Create app with the URL (OAuth). |
| Cursor | `~/.cursor/mcp.json` → `{"mcpServers":{"much-odoo":{"url":"https://<odoo>/mcp"}}}` (OAuth auto-detected). |
| VS Code | `.vscode/mcp.json` → top-level `servers` key, `type: "http"`, same URL. |
| **Hermes** | `hermes mcp add <name> --url https://<odoo>/mcp --auth oauth` (see below). |
| stdio-only | Standalone bridge: `uvx mcp-server-odoo` with `ODOO_URL`, `ODOO_API_KEY`, `ODOO_DB` env. |

Any client that supports remote HTTP MCP + OAuth works with just the URL — the module is its
own OAuth 2.1 authorization server and self-advertises via `/.well-known`.

## Hermes — OAuth (recommended)

```bash
hermes mcp add odoo_much --url https://<odoo>/mcp --auth oauth
```

What happens:

1. The CLI prints an **authorization URL** and waits.
2. Open that URL in a browser, sign in with your **Odoo** account, approve the consent
   screen. (Optional: switch off "Create and modify data" for a read-only `mcp:read` session.)
3. The browser is redirected to a **loopback callback** — `http://localhost:<port>/…?code=…&state=…`.

### The redirect gotcha (remote / headless CLI)

The callback points at `localhost` **on the machine running `hermes`**. If the browser is on
a different machine, or nothing is listening there, the page fails to load ("can't reach
this site"). That is expected — **do not** try to make localhost work. Instead:

- Copy the **entire redirected URL** from the browser's address bar
  (`http://localhost:<port>/...?code=...&state=...`), and
- **paste it back into the `hermes mcp add` prompt.** The CLI extracts the code and completes
  the token exchange.

Then verify:

```bash
hermes mcp test odoo_much           # should report "Connected" + N tools discovered
```

In a session the tools load as deferred tools named `mcp__odoo_much__<tool>` and are reached
via `tool_search` / `tool_call`. Requires `hermes -p <profile>` for the profile you added it to.

## Hermes — API key

```bash
hermes mcp add odoo_much --url https://<odoo>/mcp --auth header
# prompt: "API key / Bearer token:"  -> paste the MCP-scope key
```

The key is stored as an env var in the profile's `.env` (e.g. `MCP_ODOO_MUCH_API_KEY`) and
referenced from `config.yaml` as `Authorization: Bearer ${MCP_ODOO_MUCH_API_KEY}` — no secret
sits in the config. Mint the key in Odoo: **My Profile → Account Security → New API Key,
Scope = MCP**.

## Verify the connection by hand

```bash
# unauthenticated: expect 401 (route exists, auth required)
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://<odoo>/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}'
```

401 = endpoint live. 503 = MCP disabled (master switch off). A manual JSON-RPC session then
runs `initialize` → `notifications/initialized` → `tools/list` (reuse the `Mcp-Session-Id`
header the server returns).
