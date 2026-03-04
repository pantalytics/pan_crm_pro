# pan_crm_pro

CRM productivity addons for Odoo 19 Enterprise by Pantalytics B.V.

## Modules

| Module | Version | Description |
|--------|---------|-------------|
| [pan_crm_pro](pan_crm_pro/) | 19.0.1.4.0 | CRM productivity enhancements with AI enrichment |

## Requirements

To use the AI enrichment features, install **Pan AI Pro** (`pan_ai_pro`) from the Odoo App Store. This module adds Anthropic Claude as an AI provider to Odoo.

## Installation (Odoo.sh)

Add as git submodule in your Odoo.sh project:

```bash
cd addons
git submodule add <repo-url> pan_crm_pro
```

Then install `pan_crm_pro` from Apps.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — Technical details for developers
- [CLAUDE.md](CLAUDE.md) — AI assistant context
