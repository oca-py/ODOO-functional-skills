# Bank statement import — runbook & verified run

## Runbook

```
0. find the existing bank journal      (type="bank"; do NOT create one)
1. build the plan                      start[n] = end_real[n-1]; end_real[n] = start[n] + Σlines[n]
2. create one statement per number     account.bank.statement create with line_ids: [(0,0,{...})]
3. verify                              balance_start + Σlines == balance_end_real  AND is_valid
```

### 1. Find the journal

```python
execute_kw("account.journal", "search_read", [[("type", "=", "bank")]],
           {"fields": ["name", "code", "bank_account_id"]})
# -> [{'id': 13, 'name': 'Bank', 'code': 'BNK1', 'bank_account_id': [1, '12333MyTestBank']}]
```

The `bank_account_id` display gives the account number — that is how you recognise the right
journal when several exist.

### 2. Build the plan (this is where balances go wrong)

```python
balance = opening_balance
for period in periods:
    lines = [...eligible bookings for the period...]
    delta = sum(l["amount"] for l in lines)      # credits +, debits -
    statement = {"balance_start": balance, "balance_end_real": balance + delta, "lines": lines}
    balance += delta                             # chain to the next statement
```

Every statement must account for **every** line in its period; a missing booking or a wrong sign
shows up as a closing balance that doesn't match the bank.

### 3. Create

One `create` per statement, with the lines inline:

```python
execute_kw("account.bank.statement", "create", [{
    "name": name, "date": closing_date, "journal_id": journal_id,
    "balance_start": start, "balance_end_real": end,
    "line_ids": [(0, 0, {"date": d, "payment_ref": label, "amount": amt, "journal_id": journal_id})
                 for d, label, amt in lines],
}])
```

### 4. Verify

```python
recs = execute_kw("account.bank.statement", "read",
                  [ids, ["name", "date", "balance_start", "balance_end", "balance_end_real",
                         "is_valid", "is_complete", "line_ids"]])
for r in recs:
    lines = execute_kw("account.bank.statement.line", "read", [r["line_ids"], ["amount"]])
    assert abs(r["balance_start"] + sum(l["amount"] for l in lines) - r["balance_end_real"]) < 0.01
    assert r["is_valid"]
```

## Verified run (Odoo 20.0)

Journal **13 / BNK1**, bank account **12333MyTestBank**, currency PYG. Opening 5,000,000; 15
statements of 15 days each, chained; 52 lines total, 2–5 distinct booking dates per statement.

| # | Statement | Closing date | Start | Σ lines | End (real = computed) | Valid |
|---|---|---|---|---|---|---|
| 1 | 12333/2026/01 | 2026-01-15 | 5,000,000 | 1,482,000 | 6,482,000 | ✓ |
| 2 | 12333/2026/02 | 2026-01-30 | 6,482,000 | -696,000 | 5,786,000 | ✓ |
| 3 | 12333/2026/03 | 2026-02-14 | 5,786,000 | -84,000 | 5,702,000 | ✓ |
| 4 | 12333/2026/04 | 2026-03-01 | 5,702,000 | 87,000 | 5,789,000 | ✓ |
| 5 | 12333/2026/05 | 2026-03-16 | 5,789,000 | -311,000 | 5,478,000 | ✓ |
| 6 | 12333/2026/06 | 2026-03-31 | 5,478,000 | 315,000 | 5,793,000 | ✓ |
| 7 | 12333/2026/07 | 2026-04-15 | 5,793,000 | 715,000 | 6,508,000 | ✓ |
| 8 | 12333/2026/08 | 2026-04-30 | 6,508,000 | -257,000 | 6,251,000 | ✓ |
| 9 | 12333/2026/09 | 2026-05-15 | 6,251,000 | -253,000 | 5,998,000 | ✓ |
| 10 | 12333/2026/10 | 2026-05-30 | 5,998,000 | -997,000 | 5,001,000 | ✓ |
| 11 | 12333/2026/11 | 2026-06-14 | 5,001,000 | 907,000 | 5,908,000 | ✓ |
| 12 | 12333/2026/12 | 2026-06-29 | 5,908,000 | 184,000 | 6,092,000 | ✓ |
| 13 | 12333/2026/13 | 2026-07-14 | 6,092,000 | 645,000 | 6,737,000 | ✓ |
| 14 | 12333/2026/14 | 2026-07-29 | 6,737,000 | -476,000 | 6,261,000 | ✓ |
| 15 | 12333/2026/15 | 2026-08-13 | 6,261,000 | 817,000 | 7,078,000 | ✓ |

**15/15 balanced, `is_valid` and `is_complete` true on all, 0 mismatches.**

## Notes from the run

- The first statement opened at the starting balance, so nothing was "created" from thin air — the
  chain closes at 7,078,000 which is exactly opening + Σ all 52 lines.
- Statement `name` here is `12333/2026/NN`; the trailing number is the *statement* number, not a
  month. Pick whatever numbering your bank uses and keep it unique per statement.
- Lines were given `journal_id` even though it is related to `move_id.journal_id` — harmless and
  explicit.
- `date` on a line is related and not stored on the line itself; it lands on the generated journal
  entry.

## Attaching the statement PDF (verified)

Each statement also carries its bank document as an attachment, generated from the same data:

```
1. build the document      HTML from the statement + its lines (header, table, opening/closing)
2. render to PDF           headless Chrome Page.printToPDF (A4, printBackground)
3. attach                  ir.attachment {res_model:"account.bank.statement", res_id, type:"binary",
                           name:"12333-2026-01.pdf", raw: base64}
4. verify                  read back raw -> base64decode -> compare bytes/sha1 with the file
```

Odoo 20 specifics: the write field is **`raw`** (there is no `datas`), `mimetype` is computed and
readonly, and reading `raw` returns `{filename, content (base64), size}`.

Result on the 15 statements: 15 attachments, one per statement, `application/pdf`, ~36–40 KB each,
and the read-back bytes are identical to the generated files (sha1 match).