---
name: odoo-crm-pipeline
description: Work the Odoo CRM pipeline via API/MCP: leads, opportunities, won/lost.
module: crm
odoo_versions: ["20.0"]
models: [crm.lead, crm.stage, crm.lost.reason, crm.team, sale.order]
python_models: [crm_lead, crm_stage, crm_lost_reason, crm_team, sale_order]
tags: [odoo, crm, lead, opportunity, pipeline, api, mcp]
---

# Odoo CRM — leads, opportunities and the pipeline

How an agent creates and moves CRM records: a **lead** in, **convert** it to an **opportunity**,
move it through the **stages**, mark it **won** or **lost**, and raise a **quotation** from it.

One model holds everything: **`crm.lead`**. A "lead" and an "opportunity" are the same table,
distinguished by the **`type`** field (`lead` | `opportunity`). Stages live in `crm.stage`; the
sales teams in `crm.team`; lost reasons in `crm.lost.reason`.

Load this skill when a task says: create a lead, add an opportunity, move a deal to a stage,
mark a deal won/lost, "add a customer/company to the pipeline", quote from an opportunity.

## Model ↔ table map

| Model | Table | Role |
|---|---|---|
| `crm.lead` | `crm_lead` | Lead **and** opportunity (`type` = lead/opportunity) |
| `crm.stage` | `crm_stage` | Pipeline stages (`New`, `Qualified`, `Proposition`, `Won`, …) |
| `crm.lost.reason` | `crm_lost_reason` | Lost reasons |
| `crm.team` | `crm_team` | Sales teams |
| `sale.order` | `sale_order` | A quotation linked to the opportunity (`opportunity_id`) |

Field map: [references/models.md](references/models.md). Runbook: [references/workflows.md](references/workflows.md).

## Lifecycle

```
lead ──convert_opportunity──> opportunity ──write stage_id──> … ──action_set_won──> won
                                                   │
                                                   └── write lost_reason_id + action_set_lost ──> lost
```

`crm.lead.won_status`: `pending` → `won` | `lost`. Marking won or lost sets `date_closed` and
**archives the record** (`active = False`).

## Operations (verified on Odoo 20.0)

**1. Create a lead** (or an opportunity directly with `type="opportunity"`):

```python
lead = execute_kw("crm.lead", "create", [{
    "name": "LEAD TEST 01",
    "contact_name": "Contacto Uno",
    "email_from": "lead1@example.com",
    "phone": "+595981000001",
    "type": "lead",                  # "opportunity" to start as an opportunity
    # "partner_id": partner_id, "expected_revenue": 5000, "probability": 40,
    # "team_id": team_id, "user_id": user_id, "priority": "2", "tag_ids": [(6,0,[id])]
}])
# -> type "lead", stage "New", probability 0, won_status "pending"
```

**2. Convert a lead to an opportunity:**

```python
execute_kw("crm.lead", "convert_opportunity", [[lead], {}])   # partner_id={} => no partner linked
# -> type "opportunity" (stage stays as-is)
```

**3. Move it through the pipeline:** `execute_kw("crm.lead", "write", [[lead], {"stage_id": stage_id}])`.

**4. Mark it won:** `execute_kw("crm.lead", "action_set_won", [[lead]])`
→ stage `Won`, `probability=100`, `won_status="won"`, `date_closed` set.

**5. Mark it lost** — `action_set_lost()` takes **no arguments**, so set the reason first:

```python
execute_kw("crm.lead", "write", [[lead], {"lost_reason_id": lost_reason_id}])
execute_kw("crm.lead", "action_set_lost", [[lead]])
# -> won_status "lost", date_closed set, active=False (archived)
```

**6. Create a quotation from an opportunity** — link it with `opportunity_id`:

```python
so = execute_kw("sale.order", "create", [{
    "partner_id": partner_id,
    "opportunity_id": lead,                # sale_crm adds this field
    "order_line": [(0, 0, {"product_id": product_id, "product_uom_qty": 1,
                           "price_unit": 100.0, "tax_ids": [(6, 0, [tax_id])]})],
}])
# lead.order_ids now contains the SO
```

## MCP equivalents

| Step | MCP tool |
|---|---|
| create / update a lead | `create_record` / `update_record` (`model="crm.lead"`) |
| find leads | `search_records` (`domain`, `fields`, `limit`) |
| pipeline totals | `aggregate_records` (group by `stage_id`, sum `expected_revenue`) |
| convert / won / lost | `call_model_method` (`convert_opportunity`, `action_set_won`, `action_set_lost`) — public methods |

## Gotchas

- **One model, two types.** Do not look for a separate "opportunity" table — filter `type`.
- **`action_set_lost()` takes no arguments** (calling it with the reason raises
  `TypeError: takes 1 positional argument but 2 were given`). Write `lost_reason_id` first.
- **Won/lost archives the record** (`active=False`). A default search won't show closed deals;
  query with `context={"active_test": False}` to read them.
- **Won also jumps the stage to the "Won" stage and sets probability 100.**
- `stage_id` write does **not** change `probability` automatically unless the stage/team config says so.
- `name`, `contact_name`/`partner_id`, `email_from`/`phone` are the main lead fields; `expected_revenue`
  is the forecast amount and `date_deadline` the expected closing date.