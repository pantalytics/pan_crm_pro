# Architecture

Technical documentation for developers working on CRM Pro.

---

## Overview

**CRM Pro** adds three UX enhancements to Odoo 19 CRM:

1. **Chatter Resizer** — Drag-to-resize the form/chatter split
2. **Email Preview** — Latest email preview in kanban and list views
3. **Last Contact** — Relative timestamp of the last message

All features are non-destructive: they add computed fields and UI enhancements without modifying any core CRM behavior.

---

## Chatter Resizer

### How it works

The resizer patches `FormRenderer` (OWL component) to inject a drag handle between the form sheet and the chatter panel on XXL form views.

```
FormRenderer.setup()
  → onMounted / onPatched
    → installResizer()
      → Find .o_form_view.o_xxl_form_view
      → Find .o_form_sheet_bg + .o-mail-Form-chatter.o-aside
      → Insert .o_chatter_resize_handle between them
      → Apply saved ratio from localStorage
```

### Drag interaction

```
mousedown on handle
  → track mousemove → compute ratio from cursor X position
  → clamp to MIN_RATIO (0.2) / MAX_RATIO (0.8)
  → apply as flex ratio on sheet + chatter
mouseup
  → save ratio to localStorage (key: "pan_crm_chatter_ratio")
```

### Files

| File | Purpose |
|------|---------|
| `static/src/js/chatter_resizer.js` | OWL patch + drag logic |
| `static/src/scss/chatter_width.scss` | Handle styling (hover, active states) |

### Design decisions

- **localStorage** over server-side storage — ratio is a UI preference, not business data. No need for API calls.
- **Patch vs. inherit** — FormRenderer is patched because it's a generic OWL component, not a model-specific view. Inheritance isn't practical here.
- **Guard clause** — `installResizer()` returns early if the handle already exists, preventing duplicates on re-render.

---

## Email Preview

### Computed field

```python
x_email_preview = fields.Char(compute='_compute_email_preview')
```

- **Not stored** — recomputed on every read (emails change frequently, storage would require complex invalidation)
- Searches `mail.message` for `type=email`, ordered by `id desc`
- Uses `msg.preview` (Odoo's built-in preview text)
- Batched: one query for all leads in the recordset, then mapped by `res_id`

### Views

Injected via XPath in both kanban and list views:

| View | Position | Display |
|------|----------|---------|
| Kanban | Before `tag_ids` | `text-muted text-truncate`, hidden when empty |
| List | After `name` | Optional column (`optional="show"`) |

---

## Last Contact

### Computed field

```python
x_last_message_date = fields.Datetime(
    compute='_compute_last_message_date',
    store=True,
)
```

- **Stored** — enables sorting, grouping, and searching in list view
- `@api.depends('message_ids')` triggers recomputation when messages change
- Searches for `message_type in ('email', 'comment')` — excludes system notifications

### Timeago widget

Custom OWL field widget registered as `timeago` in the field registry.

| File | Purpose |
|------|---------|
| `static/src/js/timeago_field.js` | OWL component using Luxon's `toRelative()` |
| `static/src/xml/timeago_field.xml` | Template with tooltip for full datetime |

The widget calls `value.toRelative()` (Luxon DateTime method) to produce strings like "3 days ago", "2 hours ago". The full formatted datetime is shown as a tooltip on hover.

---

## Dependencies

| Dependency | Type | Purpose |
|------------|------|---------|
| `crm` | Odoo module | CRM lead model |
| `mail` | Odoo module | `mail.message` for email preview + last contact |
| `pan_ai_pro` | Odoo module | AI provider (enables AI-powered CRM features) |

---

## Module Manifest

```
Version:  19.0.2.0.0
License:  LGPL-3
Assets:   web.assets_backend (JS, SCSS, XML)
Data:     views/crm_lead_views.xml
```
