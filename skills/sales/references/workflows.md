# Sales — workflows & state machine

## State machine (`sale.order.state`)

```
draft ──action_quotation_sent──> sent
  │                                │
  │  action_confirm  <─────────────┘
  ▼
sale ──action_done──> (locked; invoice_status driven)
  │
  └──action_cancel──> cancel ──action_draft──> draft
```

| From | Method | To | Side effects |
|---|---|---|---|
| `draft` | `action_quotation_sent` | `sent` | Marks as sent (email flow does this too) |
| `draft`/`sent` | **`action_confirm`** | `sale` | Confirms; creates `stock.picking` deliveries; line `qty_delivered` tracking begins; unlocks invoicing |
| `sale` | `action_cancel` | `cancel` | Cancels linked pickings |
| `cancel` | `action_draft` | `draft` | Re-opens |
| `sale` | `action_done` | `sale` (locked) | Locks the order (`> 16.0`); `action_lock` on older |

**Rules:**

- **Confirm via `action_confirm`, never `write({'state':'sale'})`.** The method runs
  `_action_confirm()` which creates pickings, checks partner info, applies the pricelist
  and computes taxes.
- Confirming requires a real `partner_id`; a quotation with only a name fails validation.
- `action_quotation_sent` returns a mail-compose action — on RPC just call it and ignore
  the returned dict, or use `action_confirm` directly from `draft` (allowed and common).

## Create a full quotation

```bash
# 1) header
python scripts/odoo_rpc.py call --model sale.order --method create \
  --args '[{"partner_id": 42}]'
# -> e.g. 123

# 2) line(s) — one create per line, or a nested one2many on the header
python scripts/odoo_rpc.py call --model sale.order.line --method create \
  --args '[{"order_id": 123, "product_id": 7, "product_uom_qty": 3, "price_unit": 100.0}]'
```

Nested create (single call, same result):

```bash
python scripts/odoo_rpc.py call --model sale.order --method create \
  --args '[{"partner_id": 42, "order_line": [[0, 0, {"product_id": 7, "product_uom_qty": 3}]]}]'
```

The `order_line` one2many command triple is `[0, 0, {values}]` — the standard Odoo X2M
command format (`0=create`, `1=update`, `2=delete`, `6=set`).

## Confirm

```bash
python scripts/odoo_rpc.py call --model sale.order --method action_confirm \
  --args '[[123]]'    # pass a list of ids
```

After confirming, `state == 'sale'`, `picking_ids` is populated, and `invoice_status`
becomes `to invoice` (for `invoice_policy='order'` products) or stays `no` until delivery
(for `invoice_policy='delivery'`).

## Invoice

Invoicing is **not** a state change on the SO — it creates an `account.move`:

```bash
python scripts/odoo_rpc.py call --model sale.order --method _create_invoices \
  --args '[[123]]'
# returns an account.move recordset; read its id, then post it (accounting skill)
```

- `_create_invoices` is a private method but callable over RPC via `call`. It requires the
  order to be in `sale`.
- `invoice_status` then moves `to invoice` → `invoiced` once the move is posted.
- Posting the invoice (`account.move.action_post`) is an **accounting** operation — see the
  accounting skill before doing it.

## Delivery

For storable products, `action_confirm` creates a `stock.picking` and `delivery_status`
tracks it:

- `no` → nothing to ship (services)
- `pending` → picking created, not done
- `partial` / `full` → after pickings are validated

Validating the picking (`stock.picking.button_validate`) is an **inventory** operation —
see the inventory skill.

## Gotchas

- **Company / currency:** in multi-company DBs, create the SO in the right `company_id`,
  or Odoo raises an access error on confirm.
- **Pricelists:** omit `price_unit` to let the pricelist compute it; setting it overrides
  the pricelist for that line only.
- **Taxes:** `tax_id` defaults from the product; forcing it can break the tax report.
  Prefer leaving it unset.
- **Sequences:** `name` is auto-assigned. Don't pass it unless you need a custom reference.
- **Cancelling a confirmed order** cancels its deliveries but does **not** delete already
  posted invoices — handle those deliberately.
- **`sale.order.line` create on a confirmed order** triggers
  `_compute_amount_*` recomputes and can update `invoice_status` to `upselling`.
