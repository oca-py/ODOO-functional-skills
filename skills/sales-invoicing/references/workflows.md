# Sales invoicing — runbook & test cases

## Runbook (create → validate)

```
0. preconditions: `account` installed; a journal of type "sale"; the VAT taxes loaded.
1. partner   = search_read res.partner [("name","=",name)]  -> id, else create
2. product   = search_read product.product [("name","=",name)] -> id, else
               product.template create -> product.product search by product_tmpl_id
3. move      = account.move create {move_type:"out_invoice", partner_id, journal_id,
               invoice_line_ids:[(0,0,{product_id,name,quantity,price_unit,discount,tax_ids})]}
4. validate  = account.move action_post [move_id]
5. confirm   = account.move read [move_id] ["name","state","amount_total"]  -> state=="posted"
```

## Preconditions checked on the instance

- `account` **installed**; `sale` / `sale_management` were **not** needed (invoices are `account.move`).
- Sales journal: `INV` (`type="sale"`, id 8), default account `4.01.01 VENTAS…`.
- Sale taxes: IVA 10% (47), IVA 5% (49), Exento (51), Exonerado (53) — from `l10n_py`.
- Company: chart template `py`, currency **PYG**.

## The 20 test cases

All run against a live Odoo 20.0; **20/20 returned `posted`**.

| # | Case | Product | Partner | Result |
|---|---|---|---|---|
| 1 | existing partner + existing product, IVA 10% | existing | existing | INV/2026/00002 · 110.0 |
| 2 | qty 3, 10% discount | existing | existing | INV/2026/00003 · 149.0 |
| 3 | new partner + existing product, IVA 5% | existing | created | INV/2026/00004 · 158.0 |
| 4 | existing partner + **new** product, IVA 10% | created | existing | INV/2026/00005 · 550.0 |
| 5 | new partner + new product, Exento | created | created | INV/2026/00006 · 200.0 |
| 6 | new partner + new product, Exonerado | created | created | INV/2026/00007 · 300.0 |
| 7 | existing partner + 2 lines (10% + 5%) | existing+created | existing | INV/2026/00008 · 215.0 |
| 8 | new company w/ RUC + IVA 10%, qty 10 | existing | created | INV/2026/00009 · 1320.0 |
| 9 | individual (no VAT) + IVA 10% | existing | created | INV/2026/00010 · 99.0 |
| 10 | 3-line mixed taxes (10/5/exento) | existing+3 created | created | INV/2026/00011 · 315.0 |
| 11 | fractional quantity 2.5 | existing | existing | INV/2026/00012 · 110.0 |
| 12 | 100% discount (free) | existing | existing | INV/2026/00013 · 0.0 |
| 13 | high amount 10,000,000 PYG | created | created | INV/2026/00014 · 11,000,000.0 |
| 14 | credit note (`out_refund`) | existing | existing | RINV/2026/00001 · 110.0 |
| 15 | partner email only | existing | created | INV/2026/00015 · 88.0 |
| 16 | product with `default_code` | created | existing | INV/2026/00016 · 330.0 |
| 17 | duplicate product name → reuse existing | existing | existing | INV/2026/00017 · 165.0 |
| 18 | invoice with `ref` + `narration` | existing | created | INV/2026/00018 · 121.0 |
| 19 | reuse product on another partner | existing | created | INV/2026/00019 · 110.0 |
| 20 | new partner + product, mixed 5%/exento | created + created | created | INV/2026/00020 · 103.0 |

Post state observed: `out_invoice` 20/20 posted, `out_refund` 1/1 posted.

## Reproduce

The harness (Python, stdlib `urllib` + JSON-RPC) resolves-or-creates the product and partner,
creates the `account.move`, posts it and reads it back. Point it at any Odoo with the PY chart:

```
URL, DB, LOGIN, PASSWORD  ->  common.login  ->  object.execute_kw
```

Key call shapes are in the SKILL; the field map is in `models.md`.
