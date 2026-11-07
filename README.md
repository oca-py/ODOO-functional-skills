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
odoo_versions: ["16.0", "17.0", "18.0", "19.0"]
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

See [CONTRIBUTING.md](CONTRIBUTING.md). Add a skill under `skills/<area>/`, keep the
frontmatter schema, and cite the Odoo version you verified against.

## License

MIT — see [LICENSE](LICENSE).
