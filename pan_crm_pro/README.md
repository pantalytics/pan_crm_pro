# CRM AI Enrichment

Odoo 19 module that adds an **Enrich with AI** button to the CRM lead form.
Reads emails from the lead chatter, extracts contact data via Claude API, and
fills in missing fields on the lead and linked partner.

## Features

- On-demand enrichment from the lead form (no cron, no queue)
- Extracts: name, phone, mobile, function, company, website, address, country
- Smart merge: only fills empty fields — never overwrites existing data
- Optional website scraping for company description and industry
- Company partner deduplication by website and name
- Summary of updated fields posted to chatter

## Installation

Add as git submodule (Odoo.sh):

```bash
git submodule add <repo-url> pan_crm_pro
```

Dependencies: `crm`, `mail` (standard Odoo modules).

## Setup

1. Install the module from Apps
2. Go to **CRM > Configuration > Settings > AI Enrichment**
3. Enter your Anthropic API key (obtain at [console.anthropic.com](https://console.anthropic.com))
4. Optionally enable website scraping

## Usage

1. Open a CRM lead that has emails in the chatter
2. Click the **Enrich** button (magic wand icon) in the button box
3. Review the notification showing which fields were updated

## Data Disclosure

Email content from the lead chatter is sent to the Anthropic Claude API for
contact extraction. No data is stored externally. When website scraping is
enabled, discovered company websites are fetched and their content is also sent
to the Claude API.

## Configuration

| Setting | Description |
|---------|-------------|
| Anthropic API Key | Required. API key for Claude Haiku. |
| Website Scraping | Optional. Scrape discovered websites for company info. |

## Technical Details

- Uses `claude-haiku-4-5-20251001` (fast, low cost)
- Email text truncated to 3000 chars, website text to 2000 chars
- Country mapping via `res.country` name search
- Industry mapping via `res.partner.industry` name search
- Company dedup: search by website (ilike), then name (ilike), then create
