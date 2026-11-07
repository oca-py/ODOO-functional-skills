---
name: odoo-sales-invoicing
description: Create and validate (post) customer invoices in Odoo via API/MCP.
module: account
odoo_versions: ["20.0"]
models: [account.move, account.move.line, product.product, res.partner, account.tax, account.journal]
python_models: [account_move, account_move_line, product_product, res_partner, account_tax, account_journal]
tags: [odoo, sales, invoicing, account.move, api, mcp]
---

# Odoo sales invoicing — create & validate

How an agent creates a **customer invoice** in Odoo from a request like "invoice X to
customer Y" and **validates** it, using the API (JSON-RPC) or the MCP.

The invoice in Odoo is an **`account.move`** with `move_type = "out_invoice"` (a credit note is
`"out_refund"`). There is no separate "invoice" model, and the Sales *order* (`sale.order`) is a
different thing — for a plain invoice you write `account.move` directly.

Non-negotiable discipline (this is the whole skill):

```
resolve the product  ->  get its id  (create it if it doesn't exist)
resolve the customer ->  get its id  (create it if it doesn't exist)
create the invoice with both ids
validate it (action_post) and confirm the result
```

Never guess an id, never create a duplicate of an existing product/partner — search first.

## Model ↔ table map

| Model | Table | Role |
|---|---|---|
| `account.move` | `account_move` | The invoice / credit note |
| `account.move.line` | `account_move_line` | Invoice lines |
| `product.product` | `product_product` | The item sold (`product_id`) |
| `product.template` | `product_template` | Template (parent of the variant) |
| `res.partner` | `res_partner` | The customer (`partner_id`) |
| `account.tax` | `account_tax` | IVA 10% / 5% / Exento / Exonerado |
| `account.journal` | `account_journal` | The sales journal |

Key invoice fields and the operation/runbook are in
[references/workflows.md](references/workflows.md); the field map in
[references/models.md](references/models.md).

## The four operations

All verified against a live Odoo 20.0 (api key / JSON-RPC `execute_kw`).

**1. Resolve the customer** (search by name, then VAT/RUC):

```python
partner = execute_kw("res.partner", "search_read",
                     [[("name", "=", name)]], {"fields": ["id"], "limit": 1})
if not partner:
    partner_id = execute_kw("res.partner", "create",
                            [{"name": name, "is_company": True, "vat": vat, "email": email}])
else:
    partner_id = partner[0]["id"]
```

**2. Resolve the product** (search by name — or `default_code`):

```python
prod = execute_kw("product.product", "search_read",
                  [[("name", "=", name)]], {"fields": ["id"], "limit": 1})
if not prod:
    tmpl = execute_kw("product.template", "create",
                      [{"name": name, "type": "service", "list_price": price,
                        "sale_ok": True, "taxes_id": [(6, 0, [tax_id])]}])
    product_id = execute_kw("product.product", "search",
                            [[("product_tmpl_id", "=", tmpl)]], {"limit": 1})[0]
else:
    product_id = prod[0]["id"]
```

**3. Create the invoice** (header + lines; lines use the X2M `[0, 0, {...}]` command):

```python
move_id = execute_kw("account.move", "create", [{
    "move_type": "out_invoice",
    "partner_id": partner_id,
    "journal_id": sales_journal_id,          # the journal of type "sale"
    "invoice_line_ids": [(0, 0, {
        "product_id": product_id,
        "name": line_label,
        "quantity": 2,
        "price_unit": 100.0,
        "discount": 0.0,                     # percent
        "tax_ids": [(6, 0, [tax_id])],       # replace the line's taxes
    })],
}])
```

**4. Validate** (`action_post`) and **confirm**:

```python
execute_kw("account.move", "action_post", [[move_id]])
[rec] = execute_kw("account.move", "read", [[move_id], ["name", "state", "amount_total"]])
assert rec["state"] == "posted" and rec["name"]        # e.g. "INV/2026/00001"
```

In a draft the `name` is `False` — the sequence is assigned **on post**. That's normal, not a bug.

## MCP equivalents

Same ORM calls, through the much. Consulting **MCP Server** module (`/mcp`), if it is configured:

| Step | MCP tool |
|---|---|
| find customer/product | `search_records` (`model`, `domain`, `fields`, `limit`) |
| create them / the invoice | `create_record` (`model`, `values`) |
| validate the invoice | `call_model_method` (`model="account.move"`, `method="action_post"`, ids) — needs *Allow Method Calls* on `account.move` |
| read back | `get_record` / `search_records` |

Note: `call_model_method` only runs public business methods on models whose *Allow Method Calls*
flag is set; `action_post` qualifies. If it's off, post from the API/CLI or enable it.

## Verified

Exercised end to end on Odoo 20.0 (PY chart, PYG): **20/20 test cases passed**, producing 19
customer invoices + 1 credit note, all `posted`. Cases covered: new vs existing product and
partner in every combination, IVA 10% / 5% / Exento / Exonerado, multi-line mixed-tax invoices,
fractional quantity, 100% discount, high amounts, `ref`/`narration`, a product with
`default_code`, name-duplicate reuse, and a refund. Full case list:
[references/workflows.md](references/workflows.md#the-20-test-cases).

## Gotchas

- **`name` is empty until posted** — don't treat `name=False` as failure.
- **Taxes are an X2M**: `tax_ids: [(6, 0, [id])]` *replaces* the line's taxes; omit it to inherit
  the product's.
- **`discount` is a percentage** (0–100), not an amount.
- **`journal_id`** must be a journal of `type = "sale"` (else the posting to AR/income is wrong).
- **Credit note** = `move_type: "out_refund"` (its own sequence, `RINV/...`).
- Fractional quantities are accepted for `service` products; storable goods respect the UoM rounding.
- Amounts are **without cents semantics** on the DNIT side, but Odoo stores full precision; the
  mandatory PY partners also carry a **RUC + DV** (`l10n_py_base`) — set `vat` on company customers.
