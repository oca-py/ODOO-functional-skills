# CRM — runbook & verified flows

## Runbook

```
1. create      crm.lead create {name, contact_name|partner_id, email_from, phone, type:"lead"}
2. convert     crm.lead convert_opportunity [lead, {}]        -> type "opportunity"
3. move        crm.lead write {stage_id}
4. win         crm.lead action_set_won [lead]                 -> won, prob 100, archived
   OR lose     crm.lead write {lost_reason_id}; action_set_lost [lead]  -> lost, archived
5. quote       sale.order create {partner_id, opportunity_id, order_line:[...]}
```

## Verified on Odoo 20.0 (`crm` installed; `sales_team`, `sale_crm`, `crm_iap_enrich` pulled in)

- Create lead → `type="lead"`, stage **New**, probability 0, `won_status="pending"`.
- `convert_opportunity` → `type="opportunity"`.
- `stage_id` write → stage **Proposition**.
- `action_set_won` → stage **Won**, probability **100**, `won_status="won"`, `date_closed` set.
- `write {lost_reason_id}` + `action_set_lost` → `won_status="lost"`, `date_closed` set,
  `active=False`.
- `sale.order` create with `opportunity_id` → **S00003** linked; `lead.order_ids` = [S00003].

## CRM features (from the Odoo 20.0 docs) and their API surface

| Feature | API/ORM surface |
|---|---|
| Leads vs opportunities | `crm.lead.type` |
| Pipeline stages / Kanban | `crm.stage`, `crm.lead.stage_id` |
| Lost reasons | `crm.lost.reason`, `crm.lead.lost_reason_id` |
| Sales teams | `crm.team`, `crm.lead.team_id` |
| Lead assignment / salesperson | `crm.lead.user_id` |
| Expected revenue & forecast | `crm.lead.expected_revenue`, `probability`, `date_deadline` |
| Convert lead → opportunity | `crm.lead.convert_opportunity` |
| Won / lost | `action_set_won`, `action_set_lost` |
| Quotation from opportunity | `sale.order` with `opportunity_id` (`action_sale_quotations_new` opens a *wizard*, not a direct create) |
| Activities / meetings | `mail.activity` on the lead (`activity_ids`), `calendar.event` |
| Lead scoring / mining / enrichment | UI/IAP features (`crm_iap_enrich`); no simple ORM verb |

## Gotchas seen

- `action_set_lost()` **takes no arguments** — passing the reason raises
  `TypeError: CrmLead.action_set_lost() takes 1 positional argument but 2 were given`.
- `action_sale_quotations_new` returns an **act_window** (the "Who should be linked to this new
  Quotation?" wizard), not a created quotation — create the `sale.order` yourself with
  `opportunity_id`.
- Won/lost archives the record (`active=False`) — read with `active_test: False`.