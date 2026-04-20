# AI Demo Addon — Demo Instructions

## Overview

The **AI Demo** addon (`ai_demo`) showcases Odoo 19's AI framework for commercial sales teams. It wires a single Demo Agent to three capability topics (Leads, Sales, Activities) and provides eight ready-to-run demo flows accessible directly from the CRM Lead chatter.

Two **AI-enabled fields** are automatically populated on the Lead form when the corresponding demo flows are run:
| Field | Description |
|-------|-------------|
| `x_customer_risk_assessment` | Structured risk rating (Low/Medium/High) with financial, supply-chain and strategic risk analysis |
| `x_customer_messages_sentiment` | Sentiment analysis across all communications, with per-message emotional labels and outlier identification |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Odoo 19 (Community or Enterprise) | The `ai` core module must be installed |
| `ai`, `crm`, `sale`, `stock`, `account` modules | All are standard Odoo modules |
| An LLM configured in Settings → AI | Any supported provider (OpenAI, Azure OpenAI, etc.) |
| Demo data enabled at install time | Required to load the pre-configured TechNova scenario. Demo data loads when the **"Load demo data"** checkbox is ticked in the database creation wizard, or when `--without-demo=all` is **not** passed to `odoo-bin`. |

> **Note on invoices:** The demo creates two posted invoices automatically. If no chart of accounts is installed, invoice creation will fall back gracefully — the AI tools that read invoices will simply report "No open invoices found" instead of failing.

---

## Installation

```bash
# 1. Copy or symlink the addon into your Odoo addons path
cp -r ai_demo /path/to/odoo/addons/

# 2. Update the module list
./odoo-bin -d mydb --update=ai_demo

# Or install fresh with demo data enabled (recommended for first run):
./odoo-bin -d mydb_demo --init=ai_demo --load-language=en_US
```

After installation in **demo mode**, the following records are pre-created:
- **Partner**: TechNova Solutions (Brussels)
- **3 Products**: AI Pro Laptop 15", Universal Docking Station Pro, Professional Noise-Cancelling Headset
- **1 CRM Opportunity**: "TechNova – Q2 Hardware Renewal (50 Workstations)"
- **4 chatter notes** on the lead (call summary, customer email, stock note, voice transcription)
- **1 open activity**: follow-up call due in 3 days
- **2 confirmed sale orders** (Q4 2024 batch + Q1 2025 accessories)
- **2 posted invoices** (one 30 days overdue, one due in 25 days)

---

## Demo Scenario: TechNova Solutions

**Customer:** TechNova Solutions — a 250-person tech company in Brussels.  
**Contact:** Sophie Dumont, Head of Procurement.  
**Opportunity:** Full hardware refresh for 50 workstations. Budget: €65,000. Decision: end of Q2.  
**Current pain:** Their previous Dell supplier delivered late and sent wrong models.  
**Your angle:** Reliable logistics, full Teams/Zoom certification, competitive pricing.

This scenario is designed so that every AI tool returns meaningful, realistic data.

---

## Demo Flow 1 — Pre-Visit Report

**Goal:** In one click, get a complete briefing on the customer before a sales visit.

### Steps
1. Go to **CRM → Opportunities** and open **"TechNova – Q2 Hardware Renewal"**.
2. In the chatter, click the **AI button** (✨ icon).
3. Click the quick-access button **"Generate pre-visit report"** (or type it).
4. The agent will automatically call all context tools, then synthesise a structured HTML report.

### Expected output
```
## Pre-Visit Report – TechNova Solutions

### Financial Overview
- INV/AI-DEMO-001 | Due: [30 days ago] | Outstanding: €25,980 EUR  ← OVERDUE
- INV/AI-DEMO-002 | Due: [in 25 days] | Outstanding: €2,835 EUR

### Open Backorders
No open backorders found for this customer.

### Logistics Issues
No overdue deliveries found.

### Key Communication Highlights
- [Call note] Sophie confirmed budget, 8h battery requirement, Teams/Zoom cert needed
- [Inbound email] Formal requirements: 50 laptops + docks, 4-week delivery, 3yr warranty
- [Internal note] 30 laptop stock + need 20 more; headsets = upsell opportunity

### Recommended Actions
1. Address the €25,980 overdue invoice before the visit
2. Confirm replenishment PO for 20 additional laptops
3. Present headset bundle as value-add
```

---

## Demo Flow 2 — AI-Generated Sale Offer

**Goal:** Propose a personalised quotation based on sale history and customer needs.

### Steps
1. Open the TechNova lead.
2. Click the AI button → **"Create a sale offer based on history"**.
3. The agent reviews the two historical sale orders and the customer's email (which requests 50 laptops + docks, with headsets as optional).
4. The agent proposes a product list and asks for confirmation.
5. Confirm → the agent calls **Create Quotation** and creates a draft sale order.

### Expected dialogue
> **Agent:** Based on TechNova's order history and Sophie's email, I propose:
> - 50 × AI Pro Laptop 15" @ €1,299 = **€64,950**
> - 50 × Universal Docking Station Pro @ €249 = **€12,450**
> - 50 × Noise-Cancelling Headset @ €189 = **€9,450** *(optional, as requested)*
>
> Total (without headsets): **€77,400** — slightly over their budget. Shall I adjust the quantities or price, or confirm?

> **You:** Confirm without the headsets.

> **Agent:** Quotation S00042 created. ✅

---

## Demo Flow 3 — Suggest & Create Activities

**Goal:** Use AI to plan the right next step based on lead stage and contact history.

### Steps
1. Open the TechNova lead.
2. Click the AI button → **"Suggest activities for this lead"**.
3. The agent checks open activities and lead stage, then recommends next steps.
4. Reply: *"Create the follow-up call you suggested for next Tuesday."*
5. The agent creates the `mail.activity` directly on the lead.

### Expected output
```
Lead stage: Qualified
Days since last message: 7
Last planned activity: Phone Call due [in 3 days]

Suggested next steps:
→ Send the formal quotation before the scheduled call (stage is Qualified).
→ The existing call activity is adequate — confirm it covers the quotation review.
→ After the call, plan a 'Meeting' to present and finalise the order.
```

---

## Demo Flow 4 — Voice Transcription Summary

**Goal:** Show how the AI extracts action items from a voice call transcript.

### Steps
1. Open the TechNova lead.
2. The fourth chatter note contains a simulated voice transcription (Sophie's call from 25 March).
3. Click the AI button → **"Summarize prospect call"** (or use the Voice interface if available).
4. The agent reads the transcript and returns a Markdown summary with action items.

### Expected output
```markdown
## Call Summary — Sophie Dumont — 25 March 2025

### Key Points
- Decision deadline pushed to **end of April** (CFO request) — budget still locked ✅
- IT requests a **demo unit** (1 laptop) delivered to Sophie personally by next week

### Customer Pain Points
- Broken microphones on 4 headsets from the February order (Invoice INV/2025/0042)
  → Replacement never received — needs urgent follow-up

### Commitments Made
- We will arrange a demo unit delivery within the week
- We will investigate the headset replacement claim on INV/2025/0042

### Suggested Follow-up Activity
- **Type:** Email
- **Summary:** Send demo unit confirmation + headset replacement update
- **Deadline:** [Tomorrow's date]
```

5. Click **"Plan follow-up activity from this call"** → agent creates an Email activity with the suggested summary.

---

## Demo Flow 5 — Customer Risk Assessment *(AI-enabled field)*

**Goal:** Populate the `x_customer_risk_assessment` field with an AI-generated analysis saved directly onto the lead.

### Steps
1. Open the TechNova lead.
2. Click the AI button → **"Assess customer risk"**.
3. The agent automatically:
   - Reads open invoices, late payments, backorders, logistics issues, and sale history
   - Generates a structured risk assessment
   - **Saves the result to the `x_customer_risk_assessment` field** on the lead record

### Expected field content (after the flow)
```
Overall Risk Level: MEDIUM

Financial Risk (Medium):
- 1 overdue invoice: €25,980 outstanding, 30 days past due
- 1 upcoming invoice: €2,835 due in 25 days
- Late payment on previous invoice — monitor payment behaviour

Supply-Chain Risk (Low):
- No open backorders
- No overdue deliveries
- Stock replenishment required for 20 laptops before order confirmation

Strategic Risk (Low–Medium):
- High-value account (€65,000 opportunity)
- Active buyer with 2 confirmed orders in past 6 months
- Relationship at risk if headset replacement complaint is not resolved quickly
- Competitor (Dell) relationship strained — window of opportunity

Recommended Action:
Resolve the €25,980 overdue invoice before the visit.
Proactively address the headset replacement to avoid relationship deterioration.
Confirm demo unit delivery to maintain trust ahead of the Q2 decision.
```

> **Where to see it:** The field is visible on the Lead form in the **"AI Insights"** tab (or **"Other Info"** if no dedicated tab is configured).

---

## Demo Flow 6 — Communication Sentiment Analysis *(AI-enabled field)*

**Goal:** Populate the `x_customer_messages_sentiment` field with a per-message sentiment analysis saved directly onto the lead.

### Steps
1. Open the TechNova lead.
2. Click the AI button → **"Analyze communication sentiment"**.
3. The agent automatically:
   - Retrieves the full communication history (up to 50 messages)
   - Labels each message with an emotional tone
   - Identifies outliers
   - **Saves the result to the `x_customer_messages_sentiment` field**

### Expected field content (after the flow)
```
Overall Sentiment: MIXED (predominantly Positive with one Frustrated outlier)

Per-message breakdown:
[12 Mar 2025] Admin – Call note: Neutral/Positive — customer engaged, budget confirmed
[15 Mar 2025] Sophie Dumont – Email: Positive — clear, professional, cooperative tone
[18 Mar 2025] Admin – Stock note: Neutral — factual internal note
[25 Mar 2025] Admin – Voice transcript: FRUSTRATED (OUTLIER) — customer reports
  unresolved product defect (broken mics on 4 headsets), escalating language used:
  "nobody followed up", "still waiting"

Outliers:
⚠ 25 March transcription — frustration around headset replacement non-response.
  Risk: if left unresolved, this could jeopardise the €65,000 Q2 deal.

Actionable Summary:
Sophie is generally cooperative and positive, but the unresolved headset complaint
introduced a frustration signal. Address it immediately to preserve the relationship.
```

---

## Demo Flow 7 — Sale Order Assistant

**Goal:** Use the AI assistant directly from a Sale Order chatter.

### Steps
1. Go to **Sales → Quotations** (or **Sales → Orders**) and open any order for TechNova Solutions.
2. Click the AI button in the chatter.
3. Try: **"Suggest complementary products"** — the agent reads the order lines and queries the product catalogue to propose additions.
4. Try: **"Summarize order history for this customer"** — the agent calls sale history for the partner.
5. Try: **"Draft a follow-up email"** — the agent writes a customer-facing email body.

---

## Demo Flow 8 — General Assistant (Fallback)

When the AI button is used on a record that is not a `crm.lead` or `sale.order`, the **Demo: General Assistant** composer activates. It provides basic chatter summarisation and message drafting without domain-specific tools.

Quick buttons available:
- **"Summarize the chatter conversation"**
- **"Write a follow-up answer"**

---

## Quick Reference — All AI Buttons

### CRM Lead chatter (`chatter_ai_button`)
| Button | What it does |
|--------|--------------|
| Generate pre-visit report | Calls all 5 context tools, produces structured briefing |
| Suggest activities for this lead | Checks open activities, stage, and history; recommends next step |
| Create a sale offer based on history | Analyses orders + catalogue, proposes lines, creates quotation on confirm |
| Summarize recent communication | Returns formatted last N messages |
| **Assess customer risk** | Gathers all risk data → generates assessment → **saves to `x_customer_risk_assessment`** |
| **Analyze communication sentiment** | Reads all messages → labels emotions → **saves to `x_customer_messages_sentiment`** |

### Voice transcription on CRM Lead (`voice_transcription_component`)
| Button | What it does |
|--------|--------------|
| Summarize prospect call | Extracts key points, pain points, commitments from transcript |
| Plan follow-up activity from this call | Extracts action items, suggests activity, creates on confirm |
| Draft offer mentioned in call | Identifies products/prices mentioned, creates draft offer |

### Sale Order chatter (`chatter_ai_button`)
| Button | What it does |
|--------|--------------|
| Suggest complementary products | Cross-references order lines with product catalogue |
| Summarize order history for this customer | Returns confirmed orders with totals and products |
| Draft a follow-up email | Writes a professional customer-facing email body |

### Any other record (`chatter_ai_button` fallback)
| Button | What it does |
|--------|--------------|
| Summarize the chatter conversation | Summarises visible messages |
| Write a follow-up answer | Drafts a response to the latest message |

---

## AI-Enabled Fields Reference

Both fields live on `crm.lead` and are populated exclusively by the Demo Agent via dedicated save tools.

| Technical name | String label | How to populate |
|----------------|-------------|-----------------|
| `x_customer_risk_assessment` | Customer Risk Assessment | Click **"Assess customer risk"** in the lead chatter |
| `x_customer_messages_sentiment` | Customer Communication Sentiment | Click **"Analyze communication sentiment"** in the lead chatter |

> These fields are **read-write**: the AI writes to them, but a user can also manually edit or clear them.

---

## Demo Data Summary

Installed only when Odoo is initialised in **demo mode** (`--init` or ☑ *Demo data* in the setup wizard).

| Record | Details |
|--------|---------|
| `res.partner` | TechNova Solutions (Brussels) + contact Sophie Dumont |
| `product.template` × 3 | AI Pro Laptop 15", Universal Docking Station Pro, Noise-Cancelling Headset |
| `crm.lead` | TechNova Q2 Hardware Renewal — Qualified stage, €65k expected revenue |
| `mail.message` × 4 | Call summary, inbound email, stock note, voice transcription note |
| `mail.activity` × 1 | Follow-up call, due in 3 days |
| `sale.order` × 2 | Q4 2024 (20 laptops + docks, confirmed) · Q1 2025 (15 headsets, confirmed) |
| `account.move` × 2 | INV-001: €25,980 overdue 30 days · INV-002: €2,835 due in 25 days *(requires chart of accounts)* |

---

## Troubleshooting

### AI button not visible
- Confirm the `ai_demo` module is installed and the `ai` module is enabled.
- Check that an LLM model is configured and assigned to the Demo Agent. The exact menu path depends on your Odoo version and configuration — look under **Settings → Technical** for an **AI** or **LLM** section, or search for "AI" in the Settings search bar.

### "No open invoices found" even with demo data
- The `account.move` records require a chart of accounts to be posted. Install a localisation module (e.g. `l10n_be`) before loading demo data, or post them manually via **Accounting → Customer Invoices**.

### Fields `x_customer_risk_assessment` / `x_customer_messages_sentiment` not visible
- These fields are defined in the model but may not appear in the default form view automatically. Add them to the CRM Lead form via **Settings → Technical → User Interface → Views**, or use the Studio app to add an "AI Insights" tab.

### "Activity type not found" when creating an activity
- Ensure the standard activity types exist: Phone Call, Email, Meeting, To-Do. They are created by the `mail` module on first install.

### Demo data not loaded
- Demo data only loads when Odoo is started with the demo flag. Verify by checking **Settings → Technical → Sequences** for a `AI-DEMO` client order reference on sale orders.
- To reload: uninstall then reinstall `ai_demo` in demo mode, or run the `<function>` manually from a Python shell.
