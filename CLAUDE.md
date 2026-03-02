# Claude Code Context

Project context for Claude Code AI assistant.

## Module Overview

**pan_crm_pro** — CRM productivity addons for Odoo 19.0 Enterprise Edition.

Currently contains **pan_crm_pro**: on-demand AI contact enrichment from lead chatter emails using Claude Haiku.

## Development Principles

1. **Odoo 19 Compatibility** — Before every commit, verify code meets Odoo 19 requirements
2. **Minimal Footprint** — Stay as close to standard Odoo as possible
3. **Code Discipline** — Push back on feature requests that cause unnecessary bloat
4. **Lean Implementation** — Prefer configuration over code, reuse Odoo native features

### Odoo 19 Checklist (verify before commit)
- [ ] No `attrs` in views → use `invisible`, `readonly`, `required` directly
- [ ] No `numbercall` on cron jobs (deprecated)
- [ ] Stored computed fields have `@api.depends` decorator
- [ ] Use `groups` attribute for field access control
- [ ] XML ids follow pattern: `module_name.record_name`
- [ ] Bump version in `__manifest__.py` (format: `19.0.X.Y.Z`)

## Key Files

| File | Purpose |
|------|---------|
| `pan_crm_pro/models/crm_lead.py` | Core enrichment logic (AI call, smart merge, website scrape) |
| `pan_crm_pro/models/res_config_settings.py` | API key + website toggle settings |
| `pan_crm_pro/views/crm_lead_views.xml` | Enrich button on lead form |
| `pan_crm_pro/views/res_config_settings_views.xml` | Settings UI under CRM |

## Development

Each addon repo can be tested independently with its own `.local/` directory. A shared Dockerfile lives in the parent folder since Odoo Enterprise source is shared.

### Directory structure
```
~/Documents/GitHub/
├── .docker/
│   └── Dockerfile               ← Shared Dockerfile (Enterprise + deps)
├── odoo-enterprise/              ← Odoo 19 Enterprise source (shared)
├── pan_crm_pro/                  ← This repo
│   └── .local/                   ← Per-repo Docker config (gitignored)
│       ├── docker-compose.yml
│       └── odoo.conf
```

### Local Docker Setup
```bash
cd .local
docker-compose up -d             # Odoo at http://localhost:8069, db: test_db
```

### Restart after Python changes
```bash
cd .local
docker-compose restart odoo
```

### Upgrade module (apply model/view/data changes)
```bash
cd .local
docker-compose exec -T odoo python -m odoo -c /etc/odoo/odoo.conf -d test_db -u pan_crm_pro --stop-after-init
docker-compose restart odoo
```

### View logs
```bash
cd .local
docker-compose logs -f odoo
```

## Conventions

- All custom fields use `x_` prefix (Odoo.sh requirement)
- Log tag: `[AI Enrichment]`
- Use `invisible` instead of `attrs` in views (Odoo 19)
- Stored computed fields need `@api.depends` decorator
- Smart merge: never overwrite existing field values
- No dependency on pan_outlook_pro — works with any mail source

## Common Tasks

### Modifying the AI extraction prompt
1. Edit `EXTRACTION_PROMPT` in `pan_crm_pro/models/crm_lead.py`
2. Test with various email signatures (different formats, languages)

### Adding a new field to extract
1. Add field to `EXTRACTION_PROMPT` in `crm_lead.py`
2. Add field mapping in `_enrich_apply_lead()` or `_enrich_apply_partner()`
3. Bump version in `__manifest__.py`

### Debugging enrichment issues
1. Check Odoo logs for `[AI Enrichment]` tag
2. Verify API key is set: CRM > Configuration > Settings > AI Enrichment
3. Verify lead has email messages in chatter (type=email)

## Key Design Decisions

### On-demand only
No cron, no queue. User clicks button → enrichment runs → result shown. Simple, predictable, no unexpected API costs.

### Smart merge rule
Never overwrite existing data. Check `not getattr(self, field_name)` before writing each field.

### Company deduplication
Search order: website (ilike) → name (ilike) → create new.

## Documentation

- [README.md](README.md) — Repo overview
- [ARCHITECTURE.md](ARCHITECTURE.md) — Technical details for developers
- [pan_crm_pro/README.md](pan_crm_pro/README.md) — Module documentation

## Lessons Learned

_(Updated as issues are discovered)_
