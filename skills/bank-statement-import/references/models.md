# Bank statement — model reference (Odoo 20.0)

## `account.bank.statement` → `account_bank_statement`

| Field | Type | Notes |
|---|---|---|
| `name` | char | Statement number / reference, e.g. `12333/2026/01` |
| `reference` | char | External reference (optional) |
| `date` | date | Statement (closing) date — lines carry their own dates |
| `journal_id` | many2one `account.journal` | The existing **bank** journal |
| `balance_start` | monetary | Opening balance |
| `balance_end_real` | monetary | Closing balance **per the bank** (writable) |
| `balance_end` | monetary | **Computed** `balance_start + Σ lines` (readonly) |
| `line_ids` | one2many `account.bank.statement.line` | The bookings |
| `is_valid` | boolean | True when the declared closing matches the computed one |
| `is_complete` | boolean | Statement considered complete |
| `is_statement_posted` | boolean | Whether its entries are posted |
| `currency_id`, `company_id` | many2one | From the journal / company |

## `account.bank.statement.line` → `account_bank_statement_line`

| Field | Type | Notes |
|---|---|---|
| `statement_id` | many2one `account.bank.statement` | Set by the `[0,0,{…}]` command |
| `journal_id` | many2one `account.journal` | Required; related to `move_id.journal_id` |
| `date` | date | Related to `move_id.date`, required, **not stored** on the line |
| `payment_ref` | char | Label / description |
| `partner_id` / `partner_name` | many2one / char | Counterparty |
| `amount` | monetary | **Positive = credit (in), negative = debit (out)** |
| `amount_currency` | monetary | Amount in the account currency |
| `transaction_type` | char | Optional bank transaction type |
| `account_number` | char | Counterparty account |
| `move_id` | many2one `account.move` | The journal entry (readonly, required) |
| `is_reconciled` | boolean | Reconciled against an invoice/bill |

## Relations

```
account.journal (bank) 1 ──< n account.bank.statement 1 ──< n account.bank.statement.line ──> account.move
```

## Balance rule

```
balance_end_real = balance_start + Σ(line.amount)
balance_end      = the same sum, computed by Odoo (readonly)  → must equal balance_end_real
is_valid         = whether they match
```

A sequence of statements chains: `statement[n].balance_start == statement[n-1].balance_end_real`.