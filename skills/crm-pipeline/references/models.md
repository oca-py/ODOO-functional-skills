# CRM — model reference

## `crm.lead` → `crm_lead`

| Field | Type | Notes |
|---|---|---|
| `name` | char | Opportunity / lead title |
| `type` | selection | `lead` (Lead) or `opportunity` (Opportunity) |
| `partner_id` | many2one `res.partner` | Linked customer (optional) |
| `contact_name` | char | Contact name when there is no partner |
| `email_from` | char | Email |
| `phone` | char | Phone |
| `stage_id` | many2one `crm.stage` | Pipeline stage |
| `probability` | float | 0–100 |
| `expected_revenue` | monetary | Forecast amount |
| `date_deadline` | date | Expected closing |
| `lost_reason_id` | many2one `crm.lost.reason` | Set before marking lost |
| `won_status` | selection | `won`, `lost`, `pending` |
| `date_closed` | datetime | Set on won/lost |
| `user_id` | many2one `res.users` | Salesperson |
| `team_id` | many2one `crm.team` | Sales team |
| `tag_ids` | many2many `crm.tag` | Tags |
| `priority` | selection | `0` Low, `1` Medium, `2` High, `3` Very High |
| `active` | boolean | **False after won/lost** (archived) |
| `order_ids` | one2many `sale.order` | Quotations linked (via `sale.order.opportunity_id`) |

## `crm.stage` → `crm_stage`

`name`, `sequence`. Default pipeline: **New** (1), **Qualified** (2), **Proposition** (3),
**Won** (70).

## `crm.lost.reason` → `crm_lost_reason`

`name`. Seeded: *Too expensive*, *We don't have people/skills*, *Not enough stock*.

## `crm.team` → `crm_team`

`name`. Default team: **Sales**.

## `sale.order` (CRM link)

`sale_crm` adds **`opportunity_id`** (many2one `crm.lead`). Set it when creating the quotation so
the deal carries its `order_ids`.