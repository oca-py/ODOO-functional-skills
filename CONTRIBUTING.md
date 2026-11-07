# Contributing

## Adding a skill

1. Copy `skills/_template/` to `skills/<area>/` (area = the functional name, e.g. `sales`,
   `inventory`, `accounting`).
2. Fill the frontmatter — `module` must be the Odoo technical module name.
3. Write `SKILL.md` (the contract + quickstart) and, for anything non-trivial,
   `references/models.md` and `references/workflows.md`.
4. Verify every claim against a real Odoo instance of the versions you list. State the
   version you checked in the frontmatter `odoo_versions` array.
5. Open a PR. One module per PR.

## Rules for content

- **Verify, don't guess.** Field names, states and method names are checked against a live
  instance or the official `odoo/odoo` source for that version. No invented fields.
- **Show the operation, not just the table.** Every write path names the model method
  (`action_confirm`, `_create_invoices`, ...) and its side effects.
- **Version-flag anything that differs.** Use `> 17.0:` style callouts when a field,
  state or method changed.
- **Note the security model.** Which groups can do the operation, and any multi-company
  or record-rule implications.
- **Prefer JSON-RPC for examples** (works on Odoo Online, no extra deps); mention XML-RPC
  where relevant.
- **Never hardcode secrets.** Credentials come from env vars.

## Frontmatter schema

```yaml
name: odoo-<area>            # required, kebab-case
description: <one line>      # required, <= 60 chars
module: <odoo.technical.module>   # required
odoo_versions: ["16.0", ...]      # versions verified
models: [<dotted.model>, ...]     # required
python_models: [<table_name>, ...]
tags: [...]
```

## Review checklist

- [ ] Frontmatter present and valid
- [ ] Table names match model names (dots → underscores)
- [ ] State machines match the module
- [ ] API examples run as written
- [ ] Version notes for anything version-specific
- [ ] No secrets, no company-specific data
