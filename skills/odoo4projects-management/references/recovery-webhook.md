# Out-of-band recovery — the platform support webhook

The MCP server (`/4server/mcp`) is **part of Odoo**: it boots with the instance. If a bad
module is deployed and Odoo fails to start, the MCP is down too, and `git_pull`,
`server_restart` and `logs_grep` all time out or 500. You are then locked out of the very
tools you need to fix the instance.

The platform exposes a **control webhook outside Odoo** (an n8n endpoint) that still answers
while the instance itself is returning 500. This is the breaking-glass path.

## Endpoint

```
GET https://n8n.odoo4projects.com/webhook/ODOO4projects/support
Header: Authorization: Bearer <platform support key>     # never hardcode
Query:  action=<pull|restart|log>&uuid=<instance-db-name>
```

**Getting the key.** If you do not already have it, **ask the user to obtain a bearer key
from the chatbot at [ODOO4projects.com](https://odoo4projects.com)** and give it to you. Do
not invent one or reuse the Odoo API key. Once you have it, keep it in the environment
(e.g. `ODOO4PROJECTS_SUPPORT_KEY` in `.env`) and read it from there.

- `action` (required): `pull`, `restart` or `log`. Anything else returns
  `{"INFO":"... Actions are: pull, restart, log"}`.
- `uuid` (required): the **instance DB name** = the hostname minus the `.saopaulo` suffix,
  e.g. for `005-005-fcc3a4fe-ccbc-4e7a-b8c5-ac30a9a7528a.saopaulo` the uuid is
  `005-005-fcc3a4fe-ccbc-4e7a-b8c5-ac30a9a7528a`.

## Actions

| action | Effect | Returns |
|---|---|---|
| `log` | Reads the instance log and the git log | `{"uuid", "important_odoo_log_lines":[...], "last_git_log_lines":[...]}` — the lines are pre-grepped, newest last |
| `pull` | `git pull` on the live checkout | git output in the `message` field |
| `restart` | Restarts Odoo (needed after `pull` to rescan addons) | status message |

`log` is the fastest way to see *why* Odoo died — it does not depend on Odoo being up.

## The `pull` trap: the tip commit is reverted

`pull` fast-forwards the live checkout **and reverts the newest commit**. A fix pushed as the
tip of the branch therefore gets undone. Workaround:

```
1. push the fix                      # commit A (the fix)
2. push an empty no-op commit        # commit B, on top of A
   git commit --allow-empty -m "noop" && git push
3. action=pull                       # applies A then B, reverts only B (the no-op)
```

Now the fix (A) survives and only the throwaway no-op (B) is reverted.

## Recovery sequence for a broken deploy

```
1. action=log        -> find the traceback naming the offending module
2. fix the module ; commit ; push ; push an empty no-op commit
3. action=pull       -> live checkout gets the fix
4. action=restart    -> Odoo rescans addons and boots
5. action=log        -> confirm the ERROR|CRITICAL|Traceback is gone
```

## Notes

- **Async-safe.** Auth and routing work even while the instance itself is 500 — this is the
  out-of-band recovery path. Do not assume the webhook is broken because Odoo is.
- A branch that produces no item returns **HTTP 500** `{"code":0,"message":"No item to return
  was found"}` — harmless once the fix is in.
- After recovery, return to the MCP for the normal flow (backups, install, upgrade).

## curl example

```bash
KEY=<bearer key from the ODOO4projects.com chatbot>
UUID=005-005-fcc3a4fe-ccbc-4e7a-b8c5-ac30a9a7528a
BASE=https://n8n.odoo4projects.com/webhook/ODOO4projects/support

# 1. why did it die?
curl -s -H "Authorization: Bearer $KEY" "$BASE?action=log&uuid=$UUID" | jq .

# 2. after pushing the fix + a no-op commit
curl -s -H "Authorization: Bearer $KEY" "$BASE?action=pull&uuid=$UUID" | jq .
curl -s -H "Authorization: Bearer $KEY" "$BASE?action=restart&uuid=$UUID" | jq .
```
