---
name: odoo4projects-management
description: Operate an ODOO4PROJECTS Odoo server over its MCP: backups, git deploy, module install.
module: 4projects_server
odoo_versions: ["20.0"]
tools: [apps_list, apps_install, apps_upgrade_all, apps_update_list, backups_list, backups_create, backups_restore, logs_list, logs_grep, git_get_path, git_get_key, git_set_key, git_pull, domains_get, domains_set, server_restart]
tags: [odoo, odoo4projects, mcp, deployment, ops, module-install, recovery]
---

# ODOO4PROJECTS server management

How to run an **ODOO4PROJECTS** Odoo instance end to end through its management MCP
server: take backups, deploy addons over git, install/upgrade modules, restart, and read
the logs to confirm nothing broke.

The instance's MCP server (`4projects-odoo-server`) exposes **16 tools** — apps, backups,
logs, git, domains, server. It is the control plane for everything below.

Load this skill when a task says: install a module on the Odoo server, deploy addons,
add an OCA repo to the instance, take/restore a backup, restart Odoo, "check the logs",
recover an instance whose MCP is down after a bad deploy, or work an `odoo4projects.com`
instance.

## Connect

The MCP is **Streamable HTTP** with **Bearer** auth:

```
URL:    https://<instance>.odoo4projects.com/4server/mcp
Header: Authorization: Bearer <API_KEY>
Accept: application/json, text/event-stream
```

- The key comes from the environment (never hardcode it): `<SERVER>_API_KEY` in `.env`.
- A request without the header returns **HTTP 401**. With it, `initialize` returns 200 and
  a `Mcp-Session-Id` header; send that header on every later request.
- In Hermes, register it once with `hermes mcp add <name> --url <URL> --auth header`.
  Tools then load as `mcp__<name>__<tool>` and are reachable via `tool_search`.

Full tool list and argument schemas: [references/mcp-tools.md](references/mcp-tools.md).
The deploy/install runbook and the hard-won gotchas:
[references/workflows.md](references/workflows.md). The out-of-band recovery path:
[references/recovery-webhook.md](references/recovery-webhook.md).

## Breaking glass — when the MCP is down

The MCP lives **inside Odoo**, so if a bad module is checked in and Odoo fails to boot, the
MCP goes down with it — you lose `git_pull`, `server_restart` and `logs_grep`, exactly when
you need them. The platform still exposes a **control webhook outside Odoo** (an n8n
endpoint) that answers even while the instance returns 500:

```
GET https://n8n.odoo4projects.com/webhook/ODOO4projects/support
Header: Authorization: Bearer ***        # platform support key — never hardcode
Query:  action=<pull|restart|log>&uuid=<instance-db-name>
```

**Key:** if you do not already have the platform support key, **ask the user to get a bearer
key from the chatbot at [ODOO4projects.com](https://odoo4projects.com)** and provide it — do
not guess or reuse the Odoo API key.

- `uuid` = the **instance DB name** = the hostname minus `.saopaulo`
  (e.g. `005-005-fcc3a4fe-ccbc-4e7a-b8c5-ac30a9a7528a`).
- `action=log` → `{uuid, important_odoo_log_lines[…], last_git_log_lines[…]}` (pre-grepped,
  newest last) — the fastest way to see *why* Odoo died.
- `action=pull` → `git pull` on the live checkout; returns the git output.
- `action=restart` → restarts Odoo (needed after `pull` to rescan addons).
- Any other action → `{"INFO":"… Actions are: pull, restart, log"}`.

⚠️ **`pull` also reverts the tip commit** on the live checkout, so a fix pushed as the tip
gets undone. Push the fix, then push an **empty no-op commit** on top; `pull` applies both
and reverts only the no-op.

Recover a broken deploy: `action=log` (find the traceback) → push fix + no-op commit →
`action=pull` → `action=restart` → `action=log` to confirm. Full details:
[references/recovery-webhook.md](references/recovery-webhook.md).

## The 16 tools

| Group | Tools |
|---|---|
| Apps | `apps_list`, `apps_install`, `apps_upgrade_all`, `apps_update_list` |
| Backups | `backups_list`, `backups_create`, `backups_restore` |
| Logs | `logs_list`, `logs_grep` |
| Git | `git_get_path`, `git_get_key`, `git_set_key`, `git_pull` |
| Domains | `domains_get`, `domains_set` |
| Server | `server_restart` |

Only `logs_grep`, `git_set_key`, `domains_set`, `backups_restore` and `apps_install` take
arguments (see the reference). Everything else is callable with `{}`.

## Canonical workflow — install modules on the server

```
1. apps_list                         -> read the Odoo version (module versions are "<series>.x")
2. backups_create  + backups_list    -> BACKUP BEFORE TOUCHING ANYTHING
3. git_get_path                      -> clone URL of the instance's own repo
   git clone <url> ; add modules under custom/
   git commit ; git push
4. git_pull                          -> server fast-forwards its live checkout
5. server_restart                    -> REQUIRED: the server only rescans addons on boot
6. apps_update_list                  -> modules now appear, state "uninstalled"
7. apps_install <module>             -> one call per module, dependencies first
   (poll apps_list until state == "installed"; installs are asynchronous)
8. server_restart                    -> apply, then:
9. logs_grep  pattern "ERROR|CRITICAL|Traceback"   -> confirm nothing broke
10. backups_list                     -> confirm the pre-install backup survived
```

Steps 5 and 6 are the trap: **`git_pull` alone does not register new modules.** Without a
restart, `apps_update_list` finds nothing new and `apps_list` shows no new module.

## Best practices (non-negotiable)

1. **Match versions.** Every module's `__manifest__.py` `version` must start with the
   server's Odoo series (here `20.0`). Read the server series from `apps_list` (e.g. `base`
   is `20.0.1.3`). Install the Odoo-version branch of an OCA repo, not `main`.
2. **Backup first.** `backups_create` before adding or upgrading any module, then confirm
   the new zip with `backups_list`.
3. **Restart, then read the logs.** After install and restart, `logs_grep` for
   `ERROR|CRITICAL|Traceback`. A module that raises on load leaves a traceback; the DB
   state alone says "installed" and hides it.
4. **Install in dependency order** (or install a leaf module and let Odoo pull its deps).
   Check `depends` in each manifest; missing deps abort the install.
5. **Check `to upgrade` afterwards** — `apps_list --state "to upgrade"`; run
   `apps_upgrade_all` only if that list is non-empty.

## Deploy layout (what the instance repo is)

The instance repo `odoo.git` is the deployment definition, not module source:

```
docker-compose.yaml   # web: odoo:<series>, db: postgres:16; the volumes mount config/ custom/ enterprise/
config/odoo.conf      # addons_path = /mnt/addons/custom,/mnt/addons/enterprise ; logfile=/var/log/odoo.log
custom/               # <-- put OCA / custom addons HERE (one dir per module)
enterprise/           # enterprise addons
```

`custom/` and `enterprise/` are mounted as addon roots, so a module only becomes visible
once its directory is inside `custom/` **and** the server has restarted.

## Gotchas

- `git_pull` fast-forwards the live checkout at `/git-server/repos/local`; run it, then
  **restart**, then `apps_update_list`.
- `git_set_key` (add the deploy public key) and `domains_set` both need a **restart** to
  take effect.
- `apps_install` is asynchronous — it returns "installation initiated". Poll `apps_list`.
- Modules with `external_dependencies` (python) can fail to load if the wheel isn't in the
  image (seen: `num2words`, `python-stdnum`, `qrcode`, `requests`, `cryptography`,
  `pykude`, `sifen`). If install fails, `logs_grep` for the missing import.
- The instance's own `4projects_server` MCP middleware logs a benign
  `ImportError: cannot import name 'db' from 'odoo.service'` on Odoo 20.0 on every MCP
  request. The call still succeeds (HTTP 200). Do not mistake it for a module failure.
