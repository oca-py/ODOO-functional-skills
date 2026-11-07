# ODOO4PROJECTS — deploy & module-install runbook

The exact sequence that works, learned the hard way on an Odoo 20.0 instance.

## 0. Read the server first

```
apps_list  ->  find `base`: 20.0.1.3  => server runs Odoo 20.0
```

Install the **20.0 branch** of any OCA repo. Module `version` fields must be `20.0.x`.

## 1. Backup before anything

```
backups_create          # "Backup scheduled. It will start within the next minute."
# wait ~60s
backups_list            # newest zip is your rollback point
```

`backups_restore <filename>` overwrites the live DB — treat it as destructive.

## 2. First-time only: register a deploy SSH key

```
# locally
ssh-keygen -t ed25519 -N "" -f ~/.ssh/<key>
git_set_key  git_key="<contents of ~/.ssh/<key>.pub>"
server_restart          # the key is only active after a restart
git_get_key             # verify it now returns the key
```

`git_get_path` returns the clone URL, e.g.:
`git clone "ssh://git@<host>:2298/git-server/repos/odoo.git"`.
Clone with `GIT_SSH_COMMAND="ssh -i ~/.ssh/<key> -o StrictHostKeyChecking=accept-new"`.

## 3. Add modules to the instance repo

```
cd <repo>
cp -r /path/to/<oca-repo>/<module> custom/     # one dir per module, under custom/
rm -rf custom/*/__pycache__
git add -A && git commit -m "Add <modules>" && git push origin HEAD
```

Only modules inside `custom/` (or `enterprise/`) are on `addons_path`. Commit history is
the deployment history.

## 4. Bring it live

```
git_pull            # fast-forwards /git-server/repos/local to the pushed commit
server_restart      # REQUIRED — the addon roots are only rescanned on boot
# wait ~90s
apps_update_list    # now the new modules appear
apps_list state="uninstalled"   # sanity check the names/versions
```

**The trap:** `git_pull` without the following `server_restart` + `apps_update_list` leaves
the modules invisible. Symptom in the log:
`option addons_path, invalid addons directory '/git-server/repos/local/custom', skipped`.

## 5. Install

Install dependencies first, or install a leaf module and let Odoo resolve the graph:

```
apps_install module_name="l10n_py_base"
apps_install module_name="l10n_py"
apps_install module_name="l10n_py_account"
apps_install module_name="l10n_py_edi_base"
apps_install module_name="l10n_py_edi_sifen"
apps_install module_name="l10n_py_libros"
```

`apps_install` returns immediately ("installation initiated") — it is **asynchronous**.
Poll `apps_list` until `state == "installed"` for every module (allow ~60s per module).

## 6. Restart and read the logs

```
server_restart
# wait ~90s
logs_grep filename="odoo.log" pattern="ERROR|CRITICAL|Traceback" context=3
```

Judge noise vs. real failures:

- **Real** — a `Traceback` naming one of your modules (an import/loading error). Fix or
  roll back (`backups_restore`).
- **Benign on this platform** — `Could not set ARENA_MAX through mallopt()` (container
  warning) and `MCP middleware: cannot list databases / ImportError: cannot import name
  'db' from 'odoo.service'` (the instance's own MCP addon on Odoo 20.0; the MCP call still
  returns 200).

## 7. Confirm

```
apps_list state="to upgrade"     # must be empty; if not, apps_upgrade_all
apps_list state="installed"      # your modules now listed
backups_list                     # pre-install backup still present
```

## Worked example — OCA/l10n-paraguay on Odoo 20.0

Baseline 29 installed / 682 modules. Repo `OCA/l10n-paraguay`, branch `20.0`, 6 modules
(all `version` `20.0.x`): `l10n_py`, `l10n_py_account`, `l10n_py_base`, `l10n_py_edi_base`,
`l10n_py_edi_sifen`, `l10n_py_libros`.

- Pre-install backup `20261107_1108.zip`.
- Copied all six into `custom/`, pushed, `git_pull` (221 files), restarted, `apps_update_list`.
- Installed in dependency order; installed count went 29 → 64 (deps: `account`, `contacts`,
  `product`, `l10n_latam_invoice_document`, `base_address_extended`, …).
- Post-restart `logs_grep ERROR|CRITICAL|Traceback` → only the two benign lines above.
- `to upgrade` empty. All six `installed`.

`external_dependencies` seen in that repo (must exist in the image, else the install
tracebacks): `num2words`, `python-stdnum`, `qrcode`, `requests`, `cryptography`, `pykude`,
`sifen`. All were satisfied on this instance.
