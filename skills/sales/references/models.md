# Sales — model reference

Tables are model names with `.` → `_`. Field list is the agent-relevant subset, not the
full schema. `>` notes mark version differences.

## `sale.order` → `sale_order`

| Field | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `name` | char | Auto sequence, e.g. `S00001` / `SO0001` |
| `partner_id` | many2one `res.partner` | **Customer. Required to confirm.** |
| `partner_invoice_id` | many2one | Defaults from partner; used for the invoice address |
| `partner_shipping_id` | many2one | Defaults from partner; used for the delivery |
| `date_order` | datetime | Quotation date; set on create |
| `validity_date` | date | Quotation expiry (`> 16.0`) |
| `state` | selection | `draft`, `sent`, `sale`, `cancel` — see workflows |
| `pricelist_id` | many2one `product.pricelist` | Drives line pricing |
| `currency_id` | many2one `res.currency` | Usually from pricelist/company |
| `user_id` | many2one `res.users` | Salesperson |
| `team_id` | many2one `crm.team` | Sales team |
| `warehouse_id` | many2one `stock.warehouse` | Source warehouse (`> 15.0`) |
| `company_id` | many2one `res.company` | Multi-company scope |
| `amount_untaxed` | monetary | Computed, stored |
| `amount_tax` | monetary | Computed, stored |
| `amount_total` | monetary | Computed, stored |
| `invoice_status` | selection | `no`, `to invoice`, `invoiced`, `upselling` |
| `delivery_status` | selection | `no`, `pending`, `partial`, `full` (`> 16.0`) |
| `invoice_ids` | many2many `account.move` | Invoices generated from this SO |
| `picking_ids` | one2many `stock.picking` | Deliveries generated on confirm |
| `order_line` | one2many `sale.order.line` | Lines, inverse `order_id` |

`state` transitions are in [workflows.md](workflows.md).

## `sale.order.line` → `sale_order_line`

| Field | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `order_id` | many2one `sale.order` | **Required. `ondelete='cascade'`.** |
| `sequence` | int | Display order |
| `product_id` | many2one `product.product` | The variant sold |
| `name` | text | Line description (translated) |
| `product_uom_qty` | float | Ordered quantity |
| `product_uom` | many2one `uom.uom` | Unit of measure; must be in the product's UoM category |
| `price_unit` | float | Unit price (from pricelist unless overridden) |
| `discount` | float | Percentage, 0–100 |
| `tax_id` | many2many `account.tax` | Defaults from product |
| `price_subtotal` | monetary | `qty * price_unit * (1 - discount/100)`, excl. tax |
| `price_tax` | monetary | Computed tax amount |
| `price_total` | monetary | `price_subtotal + price_tax` |
| `qty_invoiced` | float | Computed, stored |
| `qty_delivered` | float | Computed, stored |
| `invoice_status` | selection | Rolled up from quantities |
| `state` | related | Mirrors `order_id.state` |

**`product_uom_qty` gotcha:** for `service`/`consu` products with a UoM precision of
`Units`, a float like `2.5` will be rejected. Read
`product_id.uom_id.rounding` (or the UoM's `rounding`) before writing fractional qty.

## Relations

```
res.partner (1) ──< (n) sale.order ──< (n) sale.order.line
                              │              │
                              │              └──> product.product ──> product.template
                              ├──> account.move      (invoices)
                              └──> stock.picking     (deliveries)
```

## Common reads

Quotations for a customer:

```bash
python scripts/odoo_rpc.py call --model sale.order --method search_read \
  --args '[[["partner_id","=",42],["state","in",["draft","sent"]]]]' \
  --kwargs '{"fields":["name","date_order","amount_total","state"]}'
```

Order with its lines:

```bash
python scripts/odoo_rpc.py call --model sale.order --method read \
  --args '[[ORDER_ID]]' \
  --kwargs '{"fields":["name","partner_id","amount_total","order_line"]}'
```
