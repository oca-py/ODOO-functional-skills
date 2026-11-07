---
name: odoo-bank-statement-import
description: Import bank statements into Odoo with correct opening/closing balances.
module: account
odoo_versions: ["20.0"]
models: [account.bank.statement, account.bank.statement.line, account.journal]
python_models: [account_bank_statement, account_bank_statement_line, account_journal]
tags: [odoo, accounting, bank, bank-statement, import, reconciliation]
---

# Odoo bank statement import

How to create/import **bank statements** (`account.bank.statement`) into Odoo so the numbers
add up: a **number**, a **date**, **bookings on several dates**, and a **beginning and ending
balance that match the lines**.

Load this when a task says: import a bank statement, load bank transactions, "the statement
balance doesn't match", reconcile a bank feed, or create statement lines from a file.

## The one invariant that matters

```
balance_start + Σ(line amounts) == balance_end_real
```

`balance_end` is **computed** from the lines; `balance_end_real` is what the bank says. Odoo keeps
both, and `is_valid` tells you whether they agree. Never write `balance_end` (readonly) — write
`balance_start` and `balance_end_real`, and make the lines produce exactly the difference.

Corollary for a sequence: **next statement's `balance_start` = previous statement's
`balance_end_real`**. If you chain them, the whole ledger stays coherent from the first opening
balance to the last closing one.

## Do this first: find the bank, never create one

A statement belongs to an existing **bank journal**. Do not create a bank or a journal — a real
deployment already has one, and a second one fragments the ledger.

```python
journals = execute_kw("account.journal", "search_read",
                      [[("type", "=", "bank")]], {"fields": ["name", "code", "bank_account_id"]})
# pick the one whose bank_account_id shows the account number, e.g. [1, "12333MyTestBank"] -> id 13
```

## Create a statement

```python
stmt = execute_kw("account.bank.statement", "create", [{
    "name": "12333/2026/01",              # the statement number / reference
    "reference": "BNK1-01",               # optional external reference
    "date": "2026-01-15",                 # statement (closing) date
    "journal_id": 13,                     # the existing bank journal
    "balance_start": 5000000.0,           # opening balance
    "balance_end_real": 6482000.0,        # closing balance per the bank
    "line_ids": [(0, 0, {
        "date": "2026-01-03",             # each booking keeps its OWN date
        "payment_ref": "Transferencia cliente",
        "amount": 350000.0,               # credit positive, debit negative
        "partner_name": "ACME SA",        # or partner_id
        "journal_id": 13,
    })],
}])
```

Lines are ordinary X2M commands (`[0, 0, {...}]`), so one `create` carries the whole statement.
A statement may hold **many lines on different dates** — that is normal, the `date` on the
statement is just the closing date.

## Verify before you call it done

```python
recs = execute_kw("account.bank.statement", "read",
                  [ids, ["name", "balance_start", "balance_end", "balance_end_real",
                         "line_ids", "is_valid"]])
for r in recs:
    lines = execute_kw("account.bank.statement.line", "read", [r["line_ids"], ["amount"]])
    total = sum(l["amount"] for l in lines)
    assert abs(r["balance_start"] + total - r["balance_end_real"]) < 0.01
    assert r["is_valid"]                              # Odoo agrees
```

`balance_end` (computed) must equal `balance_end_real` (declared). If they differ, `is_valid` is
False and the statement is unusable for reconciliation.

## Field map & runbook

- [references/models.md](references/models.md) — statement and line fields.
- [references/workflows.md](references/workflows.md) — the full runbook, the balance-chaining
  plan, and the verified 15-statement run.

## Gotchas

- **Sign convention:** credits (money in) are positive, debits (money out) negative. Getting this
  backwards flips the closing balance.
- **`balance_end` is computed and readonly** — write `balance_end_real` instead.
- **`date` on a line is related to its journal entry** (`move_id.date`) and is *not stored* on the
  line; it is still the right field to set when importing.
- **Don't reuse a statement `name`** for a different period — it is the statement's identity.
- **Currency** comes from the journal/company; don't force `currency_id` unless the account is in a
  foreign currency.
- **UI alternative:** Accounting → Bank → import (CSV/XLSX) writes the same models; the balance rule
  is identical. The API route is easier to automate and to validate.
- **Never create the bank/journal** to make an import fit — find the existing one.

## Verified

On Odoo 20.0, journal **BNK1 / account `12333MyTestBank`**: created **15 statements** (52 lines,
2–5 distinct dates each), chained from an opening 5,000,000 to a closing 7,078,000 PYG.
Result: **15/15 with `balance_start + Σlines == balance_end_real`**, `is_valid` and `is_complete`
true on every one.