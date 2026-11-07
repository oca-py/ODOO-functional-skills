# ODOO4PROJECTS MCP — tool reference

Server: `4projects-odoo-server v1.0.0`. Transport: Streamable HTTP, `Authorization: Bearer <key>`.
All calls are JSON-RPC 2.0 `tools/call` over `POST /4server/mcp` (after `initialize` +
`notifications/initialized`, reusing the `Mcp-Session-Id`).

## Schemas

| Tool | Arguments | Purpose |
|---|---|---|
| `apps_list` | `state?` (`installed`/`uninstalled`/`to upgrade`/`to remove`) | All modules with `name`, `display_name`, `state`, `installed_version`, `latest_version`. Omit `state` for all. |
| `apps_install` | `module_name` (required) | Install or upgrade one module by technical name. Async. |
| `apps_upgrade_all` | — | `update_list` then upgrade every installed module. |
| `apps_update_list` | — | Rescan addons on disk (Apps → Update Apps List). |
| `backups_list` | — | Backup filenames, newest first. |
| `backups_create` | — | Schedule an immediate backup. |
| `backups_restore` | `filename` (required) | Restore a backup. **Overwrites the DB.** |
| `logs_list` | — | Log files in `/mnt/logs` (e.g. `odoo.log`, `git.log`). |
| `logs_grep` | `filename` (req), `pattern` (req), `context?` (int, default 2, max 50) | Regex/plain search a log (plain or `.gz`). |
| `git_get_path` | — | `git clone` command for the instance's own repo. |
| `git_get_key` | — | Current SSH public key registered for the git server. |
| `git_set_key` | `git_key` (required) | Set the SSH public key. **Needs restart.** |
| `git_pull` | — | `git pull` the instance repo into the live env. **Needs restart.** |
| `domains_get` | — | Current domain config. |
| `domains_set` | `domain` (required) | Set domains (≤10, one per line, no scheme). **Needs restart.** |
| `server_restart` | — | Schedule an Odoo restart (within a minute). |

## Example calls (raw JSON-RPC)

```jsonc
// list installed modules
{"method":"tools/call","params":{"name":"apps_list","arguments":{"state":"installed"}}}

// backup, then confirm
{"method":"tools/call","params":{"name":"backups_create","arguments":{}}}
{"method":"tools/call","params":{"name":"backups_list","arguments":{}}}

// install a module
{"method":"tools/call","params":{"name":"apps_install","arguments":{"module_name":"l10n_py_base"}}}

// tail the log for errors
{"method":"tools/call","params":{"name":"logs_grep",
 "arguments":{"filename":"odoo.log","pattern":"ERROR|CRITICAL|Traceback","context":3}}}

// register a deploy key, then restart
{"method":"tools/call","params":{"name":"git_set_key",
 "arguments":{"git_key":"ssh-ed25519 AAAA... user@host"}}}
{"method":"tools/call","params":{"name":"server_restart","arguments":{}}}
```

## Minimal Python client

```python
import json, urllib.request
URL, KEY = "https://<instance>.odoo4projects.com/4server/mcp", "<API_KEY>"
H = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
     "Authorization": f"Bearer {KEY}"}

def _post(body, sid=None):
    h = dict(H)
    if sid: h["Mcp-Session-Id"] = sid
    r = urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), h), timeout=180)
    raw = r.read().decode()
    if not raw.strip(): return None, r.headers.get("Mcp-Session-Id")
    for line in raw.splitlines():
        if line.startswith("data:"): raw = line[5:].strip()
    return json.loads(raw), r.headers.get("Mcp-Session-Id")

def session():
    _, sid = _post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"c","version":"0"}}})
    _post({"jsonrpc":"2.0","method":"notifications/initialized"}, sid)
    return sid

def call(tool, args):
    res, _ = _post({"jsonrpc":"2.0","id":2,"method":"tools/call",
                    "params":{"name":tool,"arguments":args}}, session())
    out = res["result"]
    return "\n".join(c.get("text","") for c in out["content"]) if out.get("content") else out
```

`notifications/initialized` returns an **empty body** — handle it before `json.loads`.
