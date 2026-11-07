# ODOO Functional Skills

A versioned collection of **functional knowledge packs** that teach AI agents how to
operate Odoo modules — the data model, the business rules, the canonical workflows, and
the exact API / MCP calls to read and write each module's tables.

One folder per Odoo functional area. Each folder is a self-contained *skill* an agent can
load to answer "how do I work with this module?" without crawling the source.

## Why

Odoo's functional behaviour (states, onchange logic, security groups, multi-company,
translation, computed fields) is not obvious from the raw table schema. An agent that only
sees table columns will happily write a `sale.order` in the wrong state or skip the
`action_confirm` step. These skills encode the *how*, not just the *what*.

## How we test

The OCA-PY development team uses **HERMES Agent** (Nous Research) to test these packs.
Every skill is loaded by an agent and exercised against a live Odoo instance — read the
model, drive the workflow, run the API/MCP calls — before it lands on `20.0`. A pack that
an agent can't follow is treated as broken, not as documentation.

## Branches

One branch per Odoo version, named for the version (`20.0`, `21.0`, …), following the OCA
convention. The **default branch is `20.0`** — start every clone, PR and review there.
A skill's `odoo_versions` frontmatter lists the versions it was verified against; the
branch it lands on is the version it targets.

| Branch | Odoo version | Default |
|---|---|---|
| `20.0` | Odoo 20.0 | ✅ |

## Layout

```
ODOO-functional-skills/
├── skills/
│   ├── sales/                 # one directory per module / functional area
│   │   ├── SKILL.md           # entry point: what it is, when to use it, quickstart
│   │   └── references/
│   │       ├── models.md      # tables, key fields, relations, enums
│   │       └── workflows.md   # state machines, operations, gotchas
│   ├── _template/             # copy this to start a new skill
│   │   └── SKILL.md
├── scripts/
│   └── odoo_rpc.py            # thin JSON-RPC helper for Odoo Online / on-prem
└── README.md
```

## Skill format

Every `SKILL.md` starts with YAML frontmatter so tooling can index it:

```yaml
---
name: odoo-sales
description: Work the Odoo Sales module over API/MCP: quotations, confirm, invoice.
module: sale
odoo_versions: ["20.0"]
models: [sale.order, sale.order.line]
python_models: [sale_order, sale_order_line]
tags: [odoo, sales, quotation, sale.order]
---
```

Conventions used across all skills:

- **Model vs table** — an Odoo model `sale.order` maps to the SQL table `sale_order`
  (dots → underscores). `product.product` → `product_product`.
- **`_id` columns are foreign keys**; `x_` / `x_studio_` prefix = custom/Studio field.
- **translated fields** (`name`, `description`) live in a shadow `*_<lang>` column plus a
  JSONB `jsonb_<field>` on modern versions.
- **state fields** are the contract: respect the state machine, never `write()` a state
  you could reach with a model method (`action_confirm`, `action_done`, ...).
- Every operation is shown **XML-RPC / JSON-RPC** first (works everywhere), then the
  **MCP tool** equivalent where one exists.

## Modules covered

| Skill | Odoo module | Models | Status |
|---|---|---|---|
| [sales](skills/sales/SKILL.md) | `sale` | `sale.order`, `sale.order.line` | ✅ reference example |
| [odoo4projects-management](skills/odoo4projects-management/SKILL.md) | – (platform ops) | ODOO4PROJECTS MCP | ✅ server ops: backups, git deploy, module install |
| [odoo-mcp-server](skills/odoo-mcp-server/SKILL.md) | `mcp_server` | Odoo ORM over `/mcp` | ✅ much. Consulting MCP module: install, configure, connect |

Planned: `inventory` (`stock`), `accounting` (`account`), `purchase` (`purchase`),
`contacts` (`base`), `crm`, `mrp`, `project`.

## Using a skill

1. Load the module's `SKILL.md` for the contract and quickstart.
2. Pull `references/models.md` for the field/table map you'll read or write.
3. Pull `references/workflows.md` before any state-changing operation.
4. Drive Odoo with `scripts/odoo_rpc.py` (or the equivalent MCP tool).

### Quickstart

```bash
export ODOO_URL=https://mycompany.odoo.com
export ODOO_DB=mycompany
export ODOO_USER=agent@mycompany.com
export ODOO_PASSWORD=***            # API key recommended over password

python scripts/odoo_rpc.py call \
  --model sale.order \
  --method search_read \
  --args '[[["state","=","draft"]]]' \
  --kwargs '{"fields":["name","partner_id","amount_total"],"limit":5}'
```

## Contributing

Mechanics live in [CONTRIBUTING.md](CONTRIBUTING.md) — one module per PR, keep the
frontmatter schema, cite the Odoo version you verified against. Three kinds of help are
especially welcome:

1. **Add a skill for another module.** Anything not yet covered — `inventory` (`stock`),
   `account`, `purchase`, `crm`, `mrp`, `project`, … The uncovered modules are the biggest
   gap. One module per PR.
2. **Test with another agent chain.** We build with HERMES Agent, but the packs are meant to
   be agent-agnostic. Run a skill through your own agent/harness (Claude Code, Codex, Cursor,
   …), on your Odoo version, and tell us what worked and what broke. Help testing with other
   agent chains is welcome — open an issue or a PR with the results.
3. **Backport to an older Odoo version.** `20.0` is our reference. From our perspective a
   backport is *mainly testing*: re-verify every field, state and method against that series,
   fix what differs, and set the `odoo_versions` frontmatter to match. It lands when it's
   been tested, not when it's been copied.

## License

This repository is licensed under [AGPL-3.0](LICENSE), following OCA's default
repo license policy. An individual skill may document a different license for the
Odoo module it covers — consult that module's `__manifest__.py` `license` key.
