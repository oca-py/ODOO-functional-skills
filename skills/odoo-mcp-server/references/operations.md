# MCP Server (Odoo) — configuration, architecture & troubleshooting

## How it works (architecture)

The module lives in Odoo and speaks MCP from inside the Odoo HTTP stack — there is no
separate server process.

- **Controllers** (`controllers/`): `mcp.py` / `mcp_route.py` / `mcp_dispatcher.py` (the
  `/mcp` Streamable-HTTP JSON-RPC handler), `oauth_server.py` (OAuth 2.1 AS),
  `api.py` (REST), `auth.py`, `audit.py`, `rate_limiting.py`, `jsonrpc.py`,
  `error_sanitizer.py`, `response_utils.py`.
- **Models** (`models/`): `mcp_enabled_models` (the model whitelist + per-op flags),
  `mcp_tools_read` / `mcp_tools_write` (the built-in tools), `mcp_custom_tool` (server-action
  tools), `mcp_log` (audit), `mcp_mixin`, `res_config_settings`, `res_users_apikeys`
  (the MCP-scope key), `oauth_client` / `oauth_token` / `oauth_authorization_code`.
- **Data**: `security/security.xml` (the two groups) + `ir.access.csv`, the settings and
  menu views, an OAuth-credential GC cron and an MCP-log retention cron.

So: install adds models/views/groups/crons and mounts the routes; the actual exposure is
data-driven from `mcp_enabled_models` + settings.

## Settings reference

**Settings → MCP Server** (master switch +):

| Setting | Detail |
|---|---|
| Allow OAuth 2.1 login | On by default. System parameter `mcp_server.enable_oauth`. Turn off to accept API keys only. |
| Rate limiting / request limit | Per-user per-minute limit; `429` carries `Retry-After: 60`. |
| Audit logging + retention | `mcp_server.log_retention_days` (default 30). Daily cron deletes older rows. |
| Default / max record limits | Bound tool responses to the context window. |
| Allowed Browser Origins | System parameter `mcp_server.allowed_origins`; empty = any Origin. When set, a browser request from another Origin is refused `403` (native clients send no `Origin`, unaffected). |

## Model access & security groups

- **Settings → Technical → MCP → MCP Available Models**: add a model, then tick
  Read / Write / Create / Delete and optionally **Allow Method Calls**. Default-deny.
- Groups: **MCP User** (required to use any MCP surface) and **MCP Administrator**
  (configures; implies MCP User). Sysadmins are MCP Administrators automatically. Portal
  users can't be members. Removing MCP User revokes the user's keys/tokens immediately.

## Custom tools

Wrap a **Python Code** server action (Settings → Technical → MCP → Custom Tools): give it a
name, LLM-facing description, JSON input schema and a read-only flag. In the action code,
read args from `mcp['args']` and set `mcp['result']`. The wrapped model need not be in
_Available Models_, and the model's per-op flags do **not** gate a custom tool — access is
the action's Allowed Groups plus the caller's ACLs. Scope each action narrowly.

## Multi-database deployments

If the instance serves more than one database, `/mcp` returns `404 "No database is
selected"` until the db is resolvable. Fix: one hostname per database + `dbfilter = ^%d$`
and `proxy_mode = True` (the only option for browser OAuth), or send
`X-Odoo-Database: <db>` from API-key/Bearer clients.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `401` | No/expired credential. OAuth token not bound to this resource, or key inactive. Sign in again / re-mint the key. |
| `403` (credential valid) | User not in the **MCP User** group (audited). Add them. |
| `503` on `/mcp` | Master switch off (Settings → MCP Server). |
| `404 "No database is selected"` | Multi-db instance — see above. |
| `429` | Rate limit hit; `Retry-After: 60`, or raise the limit / disable it. |
| Model access denied | Model not in enabled list, or its op flag is off; check user group. On OAuth with read-only consent, write tools are hidden and refused. |
| Module won't install / server won't start | Ensure `authlib>=1.6.12,<1.7.0`, `defusedxml`, `packaging`. `module 'lib' has no attribute 'GEN_EMAIL'` = a newer `cryptography` got installed; keep it at the image version or upgrade `pyOpenSSL` to match. |
| OAuth keeps re-prompting | A replayed refresh token revokes the whole token family by design — sign in again. Behind a proxy, check `web.base.url` in the discovery docs. |

## License & sourcing

`mcp_server` is **Odoo Proprietary License v1.0 (OPL-1)** by much. Consulting — **free to
download** from the Odoo Apps Store (https://apps.odoo.com/apps/modules/20.0/mcp_server).
This repo documents its interface only; it does **not** redistribute the module source
(OPL-1 forbids redistribution even though the module is free). Respect the license when
deploying.
