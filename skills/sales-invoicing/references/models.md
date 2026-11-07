# Sales invoicing — model reference

Tables = model name with `.` → `_`. Agent-relevant subset.

## `account.move` → `account_move` (invoice)

| Field | Type | Notes |
|---|---|---|
| `move_type` | selection | `out_invoice` (customer invoice), `out_refund` (credit note), `in_invoice`, `in_refund`, `entry` |
| `partner_id` | many2one `res.partner` | **Required.** The customer |
| `journal_id` | many2one `account.journal` | Use a journal with `type="sale"` |
| `invoice_date` | date | Defaults to today |
| `date` | date | Accounting date (set on post) |
| `name` | char | **Empty until posted** — then `INV/2026/00001` |
| `ref` | char | Free reference (e.g. the PO number) |
| `narration` | html | Notes |
| `state` | selection | `draft` → `posted` → `cancel` |
| `invoice_line_ids` | one2many `account.move.line` | The lines (inverse `move_id`) |
| `amount_untaxed` / `amount_tax` / `amount_total` | monetary | Computed |
| `currency_id` | many2one | From the company (PYG here) |
| `l10n_latam_document_type_id` | many2one | From `l10n_latam_invoice_document`; `Factura` = code `1` |

## `account.move.line` → `account_move_line`

| Field | Type | Notes |
|---|---|---|
| `move_id` | many2one `account.move` | Header (set by the `[0,0,{...}]` command) |
| `product_id` | many2one `product.product` | The item sold |
| `name` | char | Line label |
| `quantity` | float | `2.5` accepted for `service` products |
| `price_unit` | float | Unit price |
| `discount` | float | **Percent** 0–100 |
| `tax_ids` | many2many `account.tax` | `[(6, 0, [id])]` replaces the line's taxes |
| `price_subtotal` / `price_total` | monetary | Computed |

## `product.product` / `product.template`

`name`, `default_code` (internal reference), `list_price`, `type` (`service`/`consu`/`product`),
`sale_ok`, `taxes_id` (on the **template**), `uom_id`. Creating a template auto-creates one variant:
search `product.product` by `product_tmpl_id` to get its id.

## `res.partner`

`name`, `is_company`, `vat` (RUC, e.g. `80012345-0`), `email`, `country_id`, `l10n_py_*` fiscal
fields from `l10n_py_base`.

## `account.tax` (PY)

`name` (`IVA 10%`, `IVA 5%`, `Exento`, `Exonerado`), `amount`, `type_tax_use` (`sale`/`purchase`),
`l10n_py_iva_affectation` (`1` Gravado, `2` Exonerado, `3` Exento, `4` Gravado parcial).

## `account.journal`

`name`, `code`, `type` (`sale` for customer invoices), `default_account_id`. PY journals also carry
`l10n_py_establishment`, `l10n_py_point` (used for SIFEN documents).
