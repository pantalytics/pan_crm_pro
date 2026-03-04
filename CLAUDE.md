# Claude Code Context

Project context for Claude Code AI assistant.

## Module Overview

**pan_crm_pro** — CRM productivity enhancements for Odoo 19.0 Enterprise Edition.

Three features: chatter resizer, email preview, and last contact timestamp.

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
| `pan_crm_pro/models/crm_lead.py` | Email preview + last contact computed fields |
| `pan_crm_pro/views/crm_lead_views.xml` | Kanban + list view inheritance |
| `pan_crm_pro/static/src/js/chatter_resizer.js` | Drag-to-resize form/chatter |
| `pan_crm_pro/static/src/js/timeago_field.js` | "3 days ago" OWL widget |
| `pan_crm_pro/static/src/scss/chatter_width.scss` | Drag handle styling |

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
- Use `invisible` instead of `attrs` in views (Odoo 19)
- Stored computed fields need `@api.depends` decorator
- No dependency on pan_outlook_pro — works with any mail source

## Documentation

- [README.md](README.md) — Repo overview
- [ARCHITECTURE.md](ARCHITECTURE.md) — Technical details for developers
- [pan_crm_pro/README.md](pan_crm_pro/README.md) — Module documentation
