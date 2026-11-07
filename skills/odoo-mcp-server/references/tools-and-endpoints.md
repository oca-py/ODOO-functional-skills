# MCP Server (Odoo) — tools & endpoints

Source: the module's own documentation (Odoo Apps Store, `20.0`), cross-checked against the
running instance. Applies to `mcp_server` v`20.0.2.2.0`.

## Built-in tools (17: 9 read, 8 write)

### Read

| Tool | Purpose |
|---|---|
| `search_records` | Search/filter records of an enabled model (domain, fields, limit, order). |
| `get_record` | Fetch one record by id. |
| `get_fields` | Introspect a model's fields (types, required, relations). |
| `list_models` | List models exposed via MCP (the enabled-model whitelist). |
| `aggregate_records` | Group-by / aggregate (counts, sums) over a model. |
| `read_attachment` | Dereference an `odoo://` URI → text, image block, extracted PDF/Office text, or a time-limited link. |
| `list_record_attachments` | List the files attached to a record. |
| `list_resource_templates` | List the `odoo://` resource templates the server exposes. |
| `get_current_context` | The caller's user, timezone, active/allowed companies (also sent in the `initialize` handshake). |

### Write

| Tool | Purpose |
|---|---|
| `create_record` | Create one record. |
| `create_records` | Create many records of one model, **atomic** (shared or per-record values). |
| `update_record` | Update one record. |
| `update_records` | Update many records, atomic. |
| `delete_record` | Delete a record (respects referential integrity). |
| `upload_attachment` | Attach a file to a record. |
| `post_message` | Post a chatter message on a record. |
| `call_model_method` | Call a **public business** method on a model whose *Allow Method Calls* flag is set. Refuses private (`_`-prefixed) and data-access methods (`read`/`search`/`name_search`). |

Every `tools/call` is validated against the tool's advertised JSON input schema before it
runs (required/unknown args, `type` incl. unions, `enum`, `minItems`, `items.type`); a
violation is a tool error naming the argument.

## Resources

Binary data is served on demand via `odoo://` URIs instead of inline base64:

- `odoo://record/{model}/{id}/{field}`
- `odoo://attachment/{id}`

`read_attachment` dereferences them (text inline, images as image blocks, PDF/Office as
extracted text, else a time-limited download link).

## HTTP endpoints

| Endpoint | Method | Notes |
|---|---|---|
| `/mcp` | POST | Native MCP (Streamable HTTP, JSON-RPC 2.0). Protocol revisions **2025-11-25** and **2025-06-18**, negotiated at handshake. `503` while MCP is disabled. |
| `/mcp/rpc` | POST | Legacy alias of `/mcp` (same endpoint, same auth). |
| `/.well-known/oauth-protected-resource` | GET | RFC 9728 metadata. |
| `/.well-known/oauth-authorization-server` | GET | RFC 8414 metadata. |
| `/mcp/oauth/authorize` | GET/POST | Odoo login + consent screen. |
| `/mcp/oauth/token` | POST | Token endpoint (PKCE S256). |
| `/mcp/oauth/register` | POST | Dynamic client registration (RFC 7591). |
| `/mcp/health` | GET | Health check, **no auth**. |
| `/mcp/system/info` | GET | System info. |
| `/mcp/auth/validate` | GET | Validate an API key. |
| `/mcp/models` | GET | Enabled models. |
| `/mcp/models/{model}/access` | GET | Permissions for one model. |
| `/mcp/xmlrpc/common` · `/db` · `/object` | POST | XML-RPC proxy used by the `uvx mcp-server-odoo` stdio bridge. |

## Auth model

- **OAuth 2.1**: dynamic client registration (public PKCE client), per-request consent,
  opaque access tokens (1 h) stored hashed, rotating refresh tokens with reuse detection
  (a replayed refresh token revokes the whole token family). Token is bound to the `/mcp`
  resource (RFC 8707). Scopes: `mcp:read`, `mcp:write` (computed server-side, never wider
  than requested). An unauthenticated `POST /mcp` returns `401` + RFC 9728 pointer.
- **API key**: Bearer token with scope **MCP** (works only on `/mcp`).
- Every call runs as the authenticated Odoo user; ACLs and record rules always apply.
