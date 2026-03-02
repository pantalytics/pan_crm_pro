# Architecture

Technical documentation for developers working on pan_crm_pro modules.

---

## 1. Overview

### Purpose

CRM productivity addons for Odoo 19. Currently contains one module:

- **pan_crm_pro** — On-demand AI contact enrichment from lead chatter emails.

### Repository Structure

```
pan_crm_pro/
├── ARCHITECTURE.md
├── CLAUDE.md
├── README.md
├── .gitignore
└── pan_crm_pro/
    ├── __manifest__.py
    ├── __init__.py
    ├── models/
    │   ├── crm_lead.py            # Enrichment logic (AI + merge)
    │   └── res_config_settings.py # API key + website toggle
    ├── views/
    │   ├── crm_lead_views.xml     # Enrich button on lead form
    │   └── res_config_settings_views.xml
    ├── security/
    │   └── ir.model.access.csv
    ├── static/description/
    │   └── icon.png
    └── README.md
```

---

## 2. pan_crm_pro

### Flow

```
User clicks "Enrich" button on CRM lead
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. Read chatter emails                  │
│    mail.message (type=email, limit=10)  │
│    HTML → plain text via lxml           │
│    Truncate to 3000 chars               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 2. Call Claude Haiku API                │
│    Structured extraction prompt         │
│    Returns JSON with contact fields     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 3. Smart merge — lead fields            │
│    Only fill EMPTY fields               │
│    phone, mobile, website, contact_name │
│    function, street, city, zip, country │
│    partner_name (company)               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 4. Smart merge — partner fields         │
│    If partner_id exists on lead         │
│    phone, mobile, website, function     │
│    Link to parent company (dedup)       │
└─────────────────────────────────────────┘
    │
    ▼ (optional, if website scraping enabled)
┌─────────────────────────────────────────┐
│ 5. Website scrape                       │
│    GET homepage, extract text via lxml  │
│    Send to Claude for company info      │
│    Fill: company description, industry  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 6. Post summary to chatter              │
│    Show notification with field count   │
└─────────────────────────────────────────┘
```

### Key Methods (crm_lead.py)

| Method | Purpose |
|--------|---------|
| `action_enrich_with_ai()` | Button action — orchestrates the full flow |
| `_enrich_extract_text()` | HTML → plain text from mail.message bodies |
| `_enrich_call_ai()` | Sends extraction prompt to Claude Haiku |
| `_enrich_api_request()` | Low-level Anthropic API call |
| `_enrich_parse_json()` | Parse JSON from AI response (handles code fences) |
| `_enrich_apply_lead()` | Smart merge on crm.lead fields |
| `_enrich_apply_partner()` | Smart merge on res.partner fields |
| `_enrich_find_or_create_company()` | Company dedup by website → name → create |
| `_enrich_scrape_website()` | Fetch + extract website text, call AI |
| `_enrich_apply_company()` | Apply company description + industry |

### Fields Enriched

**On crm.lead:**

| Field | Source |
|-------|--------|
| `phone` | Email signature |
| `mobile` | Email signature |
| `website` | Email signature |
| `contact_name` | Email signature / sender name |
| `function` | Email signature (job title) |
| `street` / `city` / `zip` | Email signature |
| `country_id` | Email signature (mapped via `res.country`) |
| `partner_name` | Email signature (company name) |

**On res.partner (if `partner_id` exists):**

| Field | Source |
|-------|--------|
| `phone` | Email signature |
| `mobile` | Email signature |
| `website` | Email signature |
| `function` | Email signature |
| `parent_id` | Found/created company partner |

**On parent company partner:**

| Field | Source |
|-------|--------|
| `comment` | Website scrape: company description |
| `industry_id` | Website scrape: industry (mapped via `res.partner.industry`) |

### Company Deduplication

Order of matching for parent company:

1. Search `res.partner` where `is_company=True` and `website ilike` extracted website
2. Search `res.partner` where `is_company=True` and `name ilike` extracted company name
3. Create new company partner

### Smart Merge Rule

**Never overwrite existing data.** For each field:
- If the field is already filled → skip
- If the field is empty and AI extracted a value → write

This is enforced by checking `not getattr(self, field_name)` before writing.

---

## 3. Configuration

Stored via `ir.config_parameter` (accessible in CRM settings):

| Parameter | Type | Purpose |
|-----------|------|---------|
| `pan_crm_pro.api_key` | Char | Anthropic API key |
| `pan_crm_pro.website_enabled` | Boolean | Enable website scraping |

Settings fields on `res.config.settings` use `x_` prefix (Odoo.sh requirement):
- `x_enrichment_api_key`
- `x_enrichment_website_enabled`

---

## 4. AI Integration

### API

- **Endpoint:** `https://api.anthropic.com/v1/messages`
- **Model:** `claude-haiku-4-5-20251001` (fast, low cost)
- **Auth:** `x-api-key` header with API key from settings
- **API version:** `2023-06-01`

### Prompts

Two prompts are used:

1. **Contact extraction** — extracts name, phone, company, etc. from email text
2. **Website extraction** — extracts company description and industry from homepage text

Both prompts request JSON output with `null` for missing fields.

### Cost Control

- Email text truncated to 3000 chars
- Website text truncated to 2000 chars
- Max 10 emails read per enrichment
- Claude Haiku is the cheapest model available

---

## 5. Data Disclosure

Email content from the lead chatter is sent to the Anthropic Claude API for contact extraction. When website scraping is enabled, discovered company websites are fetched and their content is also sent to the Claude API. No data is stored externally.

---

## 6. Design Decisions

### On-demand only (no cron)

Enrichment runs only when user clicks the button. No background processing, no queue, no cron. This keeps the module simple, predictable, and avoids unexpected API costs.

### No dependency on pan_outlook_pro

This module works with standard `mail.message` records regardless of how emails arrive (Outlook Pro, fetchmail, manual). No import or dependency on `pan_outlook_pro`.

### Plain API key storage

The API key is stored as `ir.config_parameter` (plain text). Unlike OAuth tokens which are user credentials, an API key is a system-level secret already protected by Odoo's access controls. Encryption would add complexity without meaningful security benefit since `ir.config_parameter` is only accessible to system admins.

### lxml for HTML parsing

Uses `lxml.html.document_fromstring()` for HTML → text conversion. lxml is bundled with Odoo, so no extra dependency needed.

---

## 7. Log Tags

| Tag | Purpose |
|-----|---------|
| `[AI Enrichment]` | All enrichment operations |

---

## 8. Dependencies

| Dependency | Type | Purpose |
|------------|------|---------|
| `crm` | Odoo module | CRM lead model |
| `mail` | Odoo module | mail.message (chatter) |
| `requests` | Python stdlib | HTTP calls to Anthropic API + website scraping |
| `lxml` | Python (bundled) | HTML → text conversion |
