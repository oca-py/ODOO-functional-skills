---
name: odoo-<area>
description: <what this lets an agent do, <= 60 chars>
module: <odoo.technical.module>
odoo_versions: ["16.0", "17.0", "18.0", "19.0"]
models: [<dotted.model>, <dotted.model>]
python_models: [<table_name>, <table_name>]
tags: [odoo, <area>]
---

# Odoo <Area> (`<module>`)

One-paragraph contract: what the module is, what an agent can do with it, and the
single most important thing not to get wrong.

Load this skill when a task mentions: <trigger words an agent would see>.

## Model ↔ table map

| Odoo model | SQL table | Meaning |
|---|---|---|
| `<dotted.model>` | `<table_name>` | … |

## Key fields at a glance

`<model>`: `<field>`, `<field>`, …

## Quickstart

```bash
export ODOO_URL=... ODOO_DB=... ODOO_USER=... ODOO_PASSWORD=...

python scripts/odoo_rpc.py call --model <model> --method <method> \
  --args '<JSON>' --kwargs '<JSON>'
```

## Gotchas

- …

<!-- Move field-level detail to references/models.md and state/operation detail to
     references/workflows.md once this file grows past ~one screen. -->
