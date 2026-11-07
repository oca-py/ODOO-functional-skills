---
name: odoo-mcp-server
description: Use the Odoo-native "MCP Server" module (much. Consulting): ORM/table access over /mcp.
module: mcp_server
odoo_versions: ["20.0"]
tools: [search_records, get_record, get_fields, list_models, aggregate_records, read_attachment, list_record_attachments, list_resource_templates, get_current_context, create_record, create_records, update_record, update_records, delete_record, upload_attachment, post_message, call_model_method]
tags: [odoo, mcp, orm, api, integration, much-consulting]
---

# Odoo "MCP Server" module (much. Consulting)

> **Free to download** — Odoo Apps Store:
> https://apps.odoo.com/apps/modules/20.0/mcp_server

The Odoo addon **`mcp_server`** ("MCP Server" by much. Consulting, OPL-1) turns the Odoo
instance itself into an **MCP server**. Install it and Odoo exposes `/mcp` — any MCP client
(Claude, ChatGPT, Cursor, VS Code, Hermes, …) connects straight to the Odoo URL and gets
**ORM / table access**: search, read, create, update, delete records, aggregate, call
whitelisted business methods, read/upload attachments. Every call runs as a **real Odoo
user** under that user's ACLs and record rules.

**Not the same thing as the ODOO4PROJECTS management MCP.** That one is the platform
control plane (16 tools: backups, git deploy, module install, logs, restart). This one is a
data-plane wrapper around Odoo's ORM. They are independent; a task about *tables/records*
uses this, a task about *the server itself* uses the other (see the
`odoo4projects-management` skill).

Load this skill when a task says: give the agent access to Odoo data/tables, connect an
assistant to Odoo via MCP, `mcp_server`, `/mcp` endpoint, "search/create/update records in
Odoo", Odoo OAuth connector.

## Lifecycle

```
install  ->  configure (Odoo settings)  ->  connect an MCP client  ->  use the tools
```

### 1. Install

It is an ordinary Odoo module. On an ODOO4PROJECTS instance use the management MCP:

```
backups_create                                   # backup first
apps_install module_name="mcp_server"
server_restart
logs_grep filename="odoo.log" pattern="mcp_server.*(ERROR|Traceback)"
```

Requires `authlib>=1.6.12,<1.7.0`, `defusedxml`, `packaging` in the Odoo Python env (the
`authlib` cap exists so it doesn't drag in a newer `cryptography` than the image ships).
Version series 16.0–20.0 exist; this repo targets **20.0** (`20.0.2.2.0` current).

### 2. Configure (Odoo UI — an admin must do this)

Regular installs the module but leaves it **off**. Configuration lives in Odoo, not in code:

1. **Settings → MCP Server** → turn on the **master switch**. Same page: allow OAuth 2.1
   login (on by default), rate limiting + limit, audit log retention, default/max record
   limits, optional Allowed Browser Origins.
2. **Settings → Technical → MCP → MCP Available Models** → add each model to expose
   (e.g. `res.partner`, `sale.order`) and set **per-operation** flags: Read / Write /
   Create / Delete, plus **Allow Method Calls** (opt-in for `call_model_method`, default
   off). Default-deny: nothing is exposed until added.
3. **Security groups** (created by the module): a user must be in **MCP User** to use any
   MCP surface; **MCP Administrator** configures it. Removing MCP User instantly cuts off
   that user's keys/tokens.

### 3. Connect a client

Two auth paths — **OAuth 2.1** (recommended; no secret to copy) or an **MCP-scope API key**:

- **OAuth** — point the client at `https://<odoo>/mcp` and sign in with a normal Odoo login,
  then approve the consent screen (a "Create and modify data" switch narrows the session to
  read-only). For Hermes: `hermes mcp add <name> --url https://<odoo>/mcp --auth oauth`.
- **API key** — My Profile → Account Security → New API Key, **Scope = MCP** (an MCP key
  works *only* on `/mcp`, so a leak can't reach general RPC), send `Authorization: Bearer <key>`.

The full Hermes connect walkthrough — including the OAuth redirect that lands on a dead
`localhost` address — is in [references/connecting-clients.md](references/connecting-clients.md).

### 4. Tools

17 built-in tools (9 read, 8 write) — `search_records`, `get_record`, `get_fields`,
`list_models`, `aggregate_records`, `read_attachment`, `list_record_attachments`,
`list_resource_templates`, `get_current_context`; `create_record`, `create_records`,
`update_record`, `update_records`, `delete_record`, `upload_attachment`, `post_message`,
`call_model_method`. Full signatures, resources and HTTP endpoints:
[references/tools-and-endpoints.md](references/tools-and-endpoints.md).

## Hard-won operator notes

- **OAuth on a headless/remote box:** after you approve in the browser, the redirect goes to
  `http://localhost:<port>/callback?...` on *the client machine*. If the browser can't reach
  that (different machine / no listener), copy the whole redirected `localhost` URL back into
  the CLI prompt — that completes the exchange. See the connecting reference.
- A **403** with a valid credential means the user is not in **MCP User** (audited).
- A **503** on `/mcp` means the master switch is off. **429** = rate limit (`Retry-After: 60`).
- **Multi-database** Odoo returns `404 "No database is selected"` on `/mcp` until the db is
  resolvable — use host→db mapping (`dbfilter`) for browser OAuth, or send
  `X-Odoo-Database: <db>` with an API key.
- **Custom tools bypass** a model's per-operation flags — they run the wrapped server
  action under the caller's ACLs. Scope them narrowly.
- This module is **OPL-1**: do not redistribute its source in this repo; document behaviour only.
