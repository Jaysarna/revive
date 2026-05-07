# Revive Sustainable — ERPNext Project Plan

## Context

Revive Sustainable requires a full ERPNext configuration, customization, and workflow build-out
across CRM, sales, taxation, permissions, and social media automation. This document is the
master reference for all milestones and will live at `/home/frappe/frappe-bench/apps/revive/PLAN.md`
so it is always accessible in the codebase.

The app lives at: `/home/frappe/frappe-bench/apps/revive/`
The ERPNext instance is hosted at: `https://revive.m.frappe.cloud`

---

## Milestone Overview

| # | Milestone | Area | Status |
|---|-----------|------|--------|
| 1 | Taxation & Accounting Configuration (India Compliance) | Finance | Pending |
| 2 | Document Print Format Templates | Sales Docs | Pending |
| 2A | Project-Based Custom Quotation Templates | Sales / Projects | Pending — details TBD |
| 3 | Role-Based Permissions & Security | Security | Pending |
| 4 | Lead Module Enhancement | CRM | Pending |
| 5 | Leads List Page Customization | CRM | Pending |
| 6 | Manual Item Entry in Sales Docs | Sales | Pending |
| 7 | Social Media Workflow Automation | Marketing | Pending |

---

## Milestone 1 — Taxation & Accounting Configuration (via India Compliance App)

**Goal:** GST calculation is handled entirely by the **India Compliance** app. No custom tax logic needs to be built — configuration only.

### Approach
- India Compliance provides CGST, SGST, IGST, and export (zero-rated) heads automatically
- Integrates natively with Quotation, Sales Invoice, and Purchase flows
- GST registration, HSN/SAC code mapping, e-Invoice, and GSTR reports are covered out of the box

### Tasks
- [ ] Confirm India Compliance app is installed on the Frappe Cloud instance
- [ ] Complete **GST Settings**: GSTIN, state code, filing frequency
- [ ] Map HSN/SAC codes on all Item records
- [ ] Verify Tax Category auto-detection (In-state vs Out-of-state) on Quotation and Sales Invoice
- [ ] Confirm CGST+SGST vs IGST split based on customer state

### Files
- No custom code needed — pure configuration through ERPNext UI + India Compliance settings

---

## Milestone 2 — Document Print Format Templates

**Goal:** Branded, professional print templates for all three sales documents.

### Documents
1. **Quotation**
2. **Proforma Invoice**
3. **Sales Invoice**

### Requirements per template
- Company logo + branding header
- Digital signature block (Authorized Signatory)
- Payment Terms section
- Itemized table with HSN/SAC codes
- Tax breakdown (CGST / SGST / IGST / Total)
- Footer with company registration, GSTIN, bank details

### Implementation approach
- Use Frappe's **Print Format Builder** (HTML/Jinja2) for full control
- Store HTML templates as `.html` files under `revive/revive/print_formats/`
  - `quotation_revive.html`
  - `proforma_invoice_revive.html`
  - `sales_invoice_revive.html`
- Export as fixtures via `bench export-fixtures` for version control

---

## Milestone 2A — Project-Based Custom Quotation Templates

**Goal:** Create distinct Quotation print formats and/or item templates tied to specific project types and capacities (e.g., solar installation by kW size, waste management by volume, etc.).

> **Status: Details pending** — client will provide project type categories and capacity tiers.

### Expected Approach (to be confirmed)
- Define **Project Types** as a custom field or linked DocType on Quotation
- Each project type maps to a specific **Print Format** or a pre-filled **Items Template** (via `Quotation Template` or custom logic)
- Capacity tiers (e.g., 1 kW, 5 kW, 10 kW) may map to different line-item sets, pricing, or scope-of-work sections in the print format

### Likely Implementation
- [ ] Create a `Project Type` DocType (or Select field) to categorize quotations
- [ ] Create **Quotation Templates** per project type in ERPNext (pre-fills items + rates)
- [ ] Create corresponding **Print Formats** per project type with relevant scope/technical sections
- [ ] Client script to auto-load the correct template when a project type is selected

### Files (anticipated)
- `revive/revive/doctype/project_type/` — if a custom DocType is needed
- `revive/revive/print_formats/` — one HTML file per project type template
- `revive/revive/public/js/quotation.js` — client script for auto-template loading

> **Next step:** Awaiting project type list and capacity details from client.

---

## Milestone 3 — Role-Based Permissions & Security

**Goal:** Audit all user roles and fix any "Permission Denied" errors blocking the workflow.

### Tasks
- [ ] Review all roles in **Role Permission Manager** for these DocTypes:
  - Quotation
  - Proforma Invoice / Sales Invoice
  - Lead
  - Social Media Post (custom DocType from M7)
- [ ] Ensure correct permission levels (Read / Write / Create / Submit / Cancel / Amend) per role:
  - `Sales User` — full CRUD on Quotation, Lead
  - `Accounts User` — Submit/Cancel Sales Invoice
  - `Digital Marketing Manager` — full access to Social Media Post
  - `Intern` — Read-only on Social Media Post analytics
  - `Founder` — Read all
- [ ] Fix and document any active "Permission Denied" errors
- [ ] Test each role by logging in as a test user

---

## Milestone 4 — Lead Module Enhancement (Custom Development)

**Goal:** Convert the single-select `domain` field on Lead into a multi-select field for industry tracking.

### Approach
Use **Table Multiselect** (child DocType) since ERPNext does not natively support multi-select Link fields cleanly.

### Tasks
- [ ] Create a new child DocType: `Lead Industry Domain`
  - Fields: `domain` (Link → `Industry Type`)
- [ ] Add a **Table Multiselect** field to the Lead DocType named `industry_domains` linking to `Lead Industry Domain`
- [ ] Hide / deprecate the old `domain` field (do not delete — data migration risk)
- [ ] Write a **data migration script** to copy existing `domain` values into the new table field
- [ ] Ensure `industry_domains` is available in:
  - Lead List view (Milestone 5)
  - Reports / custom reports

### Files
- `revive/revive/doctype/lead_industry_domain/` — new child DocType
- `revive/revive/patches/` — migration patch script
- `revive/revive/hooks.py` — register patch

---

## Milestone 5 — Leads List Page Customization

**Goal:** Customize the Lead list view to show business-relevant columns.

### Desired columns (confirm with team)
- Lead Name
- Company
- Industry Domains (from M4)
- Lead Owner
- Status
- Source
- Mobile No
- Created On

### Implementation
- Use **Customize Form → List Settings** to pin columns in the List View
- Or set `list_view_fields` in the Lead DocType's JSON if managed via custom app
- Store the customization as a fixture in `revive/revive/fixtures/custom_field.json`

---

## Milestone 6 — Manual Item Entry in Sales Documents

**Goal:** Allow users to type item names freely in Quotation / Proforma Invoice / Sales Invoice without requiring the item to exist in the Item master.

### Approach
Enable the **"Allow Items not in Item list"** option:
- Go to `Selling Settings` → enable `"Allow Item to be added multiple times in a transaction"`
- More importantly: enable custom script to allow free-text entry, OR use the built-in **"Allow Item without Item Code"** option in Sales settings

### Tasks
- [ ] Check `Selling Settings` and `Stock Settings` for the relevant toggle
- [ ] If not available natively, write a **Client Script** on Quotation/Sales Invoice to allow a blank `item_code` with a manually entered `item_name` and `rate`
- [ ] Test end-to-end: create a Quotation with a manual line item and submit it

### Files
- `revive/revive/public/js/` — client scripts (if custom JS needed)

---

## Milestone 7 — Social Media Workflow Automation (Custom DocType)

**Goal:** A standalone, automated 4-stage workflow for the social media posting cycle — isolated from Task/Project permissions.

### Custom DocType: `Social Media Post`

#### Fields
| Field | Type | Notes |
|-------|------|-------|
| `post_title` | Data | Post name/title |
| `platform` | Select | LinkedIn, Instagram, etc. |
| `post_date` | Date | Scheduled date |
| `status` | Select | Draft → Completed → Shared → Monitoring → Done |
| `completed_by` | Link (User) | DMM who posted |
| `shared_at` | Datetime | Timestamp of team share acknowledgment |
| `one_hour_alert_sent` | Check | Flag |
| `twentyfour_hour_alert_sent` | Check | Flag |

#### Workflow Stages

```
[Draft]
  ↓ DMM clicks "Post Completed" button
[Completed] → Notification to Founder (Email + System)
  ↓ Founder/Team clicks "Liked & Shared on LinkedIn"
[Shared] → Notification to Interns: "Begin monitoring"
  ↓ (immediate) Scheduled Job: +1 hour
[Monitoring] → Alert to Interns: "Report 1-hour analytics"
  ↓ Scheduled Job: +24 hours
[Done] → Alert to Interns: "Report 24-hour analytics"
```

#### Implementation
- [ ] Create `Social Media Post` DocType with fields above
- [ ] Create **ERPNext Workflow** on the DocType with states and transitions
- [ ] Add **Custom Buttons** via client script: "Post Completed", "Liked & Shared"
- [ ] Create **Notification** triggers for:
  - On status → Completed: email/system alert to Founder role
  - On status → Shared: system alert to Intern role
- [ ] Create **Scheduled Jobs** (using `frappe.utils.scheduler` or `Scheduled Job Type` DocType):
  - 1 hour after `shared_at`: send alert to Interns, set `one_hour_alert_sent = 1`
  - 24 hours after `shared_at`: send alert to Interns, set `twentyfour_hour_alert_sent = 1`
- [ ] Set Role Permissions (see Milestone 3)

#### Files
- `revive/revive/doctype/social_media_post/` — DocType definition
- `revive/revive/doctype/social_media_post/social_media_post.py` — server-side logic
- `revive/revive/doctype/social_media_post/social_media_post.js` — custom buttons
- `revive/revive/hooks.py` — register scheduled tasks

---

## Execution Order & Dependencies

```
M3 (Permissions) ──────────────────────────────────────┐
M1 (Tax Setup) → M2 (Print Formats)                    │
M4 (Lead Enhancement) → M5 (Lead List)                 ├─ All can run in parallel
M6 (Manual Items) — independent                        │
M7 (Social Media Workflow) — independent               ┘
```

Recommended execution sequence:
1. **M3** first — unblock workflow issues immediately
2. **M1 + M4** in parallel — foundational data setup
3. **M2 + M5** after their dependencies
4. **M6** — quick win, can do anytime
5. **M7** — most complex, save for last

---

## Testing & Verification

| Milestone | Verification Method |
|-----------|-------------------|
| M1 | Create a test Quotation — confirm correct tax template auto-fetches |
| M2 | Print preview each document — check branding, signature, tax table |
| M3 | Log in as each role — confirm access and no permission errors |
| M4 | Open a Lead — select multiple domains, save, verify in report |
| M5 | Open Lead list — confirm all desired columns visible |
| M6 | Add a free-text item to a Quotation — save and submit |
| M7 | Full end-to-end: create post → complete → share → check timed alerts |

---

## Notes

- All custom DocTypes and fixtures should be committed to the `revive` app for version control
- Run `bench migrate` after any DocType or fixture changes
- Use `bench export-fixtures` to capture configuration changes back into code
- The ERPNext instance is on Frappe Cloud — changes via UI are reflected in the cloud DB but must be exported to the app for persistence across deploys
