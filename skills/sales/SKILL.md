---
name: odoo-sales
description: Work the Odoo Sales module over API/MCP: quotations and orders.
module: sale
odoo_versions: ["16.0", "17.0", "18.0", "19.0"]
models: [sale.order, sale.order.line]
python_models: [sale_order, sale_order_line]
tags: [odoo, sales, quotation, sale.order, sale.order.line]
---

# Odoo Sales (`sale`)

How an agent reads and writes the Odoo **Sales** module: quotations, confirmed sales
orders, their lines, and the downstream invoice / delivery.

Load this skill when a task mentions: quotation, quote, sales order, `sale.order`,
confirm an order, "create a sale for customer X", sales line, order total.

## Model ↔ table map (memorise this)

| Odoo model | SQL table | Meaning |
|---|---|---|
| `sale.order` | `sale_order` | Quotation / sales order header |
| `sale.order.line` | `sale_order_line` | One product line on an order |
| `res.partner` | `res_partner` | Customer (`partner_id`) |
| `product.product` | `product_product` | Sellable variant (`product_id`) |
| `product.template` | `product_template` | Product template (parent of variants) |
| `account.move` | `account_move` | The customer invoice created from the SO |
| `stock.picking` | `stock_picking` | The delivery order created on confirm |

Dots become underscores. Details, field-by-field, in
[references/models.md](references/models.md). State machine and operations in
[references/workflows.md](references/workflows.md).

## The three things that trip agents up

1. **A quotation *is* a `sale.order`.** Same model, same table — `state` distinguishes
   `draft`/`sent` (quotation) from `sale` (confirmed order). Do not look for a separate
   "quotation" model.
2. **Never `write` `state` directly.** Move through the model's methods
   (`action_confirm`, `action_cancel`, ...) so computed fields, stock and accounting
   side effects fire. A raw `state = 'sale'` write corrupts the order.
3. **`partner_id` and `product_id` are `many2one`** — pass the integer `id`, not a name.
   Resolve names with a `search` on the target model first.

## Key fields at a glance

`sale.order`: `name` (auto, e.g. `S00001`), `partner_id`, `date_order`, `state`,
`amount_untaxed`, `amount_tax`, `amount_total`, `currency_id`, `invoice_status`,
`delivery_status`, `order_line` (one2many), `company_id`.

`sale.order.line`: `order_id`, `product_id`, `name` (description),
`product_uom_qty`, `price_unit`, `discount` (%), `price_subtotal`, `price_tax`,
`price_total`.

## Quickstart

Env (API key strongly preferred over a password on Odoo Online):

```bash
export ODOO_URL=https://mycompany.odoo.com
export ODOO_DB=mycompany
export ODOO_USER=agent@mycompany.com
export ODOO_PASSWORD=<api-key>
```

**1. Find the customer (many2one needs an id):**

```bash
python scripts/odoo_rpc.py call --model res.partner --method search_read \
  --args '[[["name","ilike","Acme"]]]' \
  --kwargs '{"fields":["name","email"],"limit":5}'
```

**2. Create a quotation with one line** (create the header, then the line — lines carry
`order_id`):

```bash
# header
python scripts/odoo_rpc.py call --model sale.order --method create \
  --args '[{"partner_id": 42}]'

# line  (replace ORDER_ID with the id returned above)
python scripts/odoo_rpc.py call --model sale.order.line --method create \
  --args '[{"order_id": ORDER_ID, "product_id": 7, "product_uom_qty": 3, "price_unit": 100.0}]'
```

**3. Confirm it** (draft → sale; triggers stock + invoice readiness):

```bash
python scripts/odoo_rpc.py call --model sale.order --method action_confirm \
  --args '[[ORDER_ID]]'
```

**MCP equivalent** (where an Odoo MCP tool is wired up):

```
odoo_create(model="sale.order", values={"partner_id": 42})
odoo_call(model="sale.order", method="action_confirm", ids=[ORDER_ID])
```

See [references/workflows.md](references/workflows.md) for invoice creation, delivery,
cancellation and the full state machine, and the gotchas (company/currency, pricelists,
taxes, `product_uom`).
