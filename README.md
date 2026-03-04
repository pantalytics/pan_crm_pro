<p align="center">
  <img src="pan_crm_pro/static/description/icon.png" alt="CRM Pro" width="128" />
</p>

<h1 align="center">CRM Pro</h1>

<p align="center">
  <strong>Productivity enhancements for Odoo 19 CRM</strong><br>
  Resizable chatter, email previews in kanban &amp; list, and relative timestamps — small tweaks that make a big difference.
</p>

<p align="center">
  <a href="https://github.com/pantalytics/pan_crm_pro/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-LGPL--3-blue.svg" alt="License: LGPL-3"></a>
  <img src="https://img.shields.io/badge/Odoo-19-purple.svg" alt="Odoo 19">
</p>

> **Note**
> This project is under active development. Features and APIs may change without notice.

---

## Features

### Chatter Resizer

Drag the boundary between the form and chatter to resize. Your preferred width is saved in the browser and persists across sessions.

- Works on any form view with a side chatter (XXL layout)
- Drag handle with visual feedback on hover
- Ratio saved per browser via `localStorage`
- Min/max bounds (20%–80%) prevent accidental collapse

### Email Preview

See the latest email preview directly in kanban cards and list view — no need to open every lead.

- Shows the preview text of the most recent inbound email
- Truncated with CSS for clean display
- Hidden when no emails exist

### Last Contact

Relative timestamp ("3 days ago") showing when the last message was posted on a lead.

- Computed from `mail.message` (emails and comments)
- Stored field — searchable, sortable, groupable
- Custom `timeago` OWL widget with tooltip showing the full date
- Updates automatically when new messages arrive

---

## Installation

### Prerequisites

- Odoo 19 Enterprise with the CRM module installed

### Optional dependency

For AI-powered features like smart field enrichment and auto-fill, install [Pan AI Pro](https://github.com/pantalytics/pan_ai_pro) (`pan_ai_pro`). CRM Pro declares it as a dependency — install it first.

### Odoo.sh

Add as a Git submodule:

```bash
git submodule add https://github.com/pantalytics/pan_crm_pro.git addons/pan_crm_pro
git commit -m "Add pan_crm_pro submodule"
git push
```

### Self-hosted

Clone into your addons path:

```bash
cd /path/to/odoo/addons
git clone https://github.com/pantalytics/pan_crm_pro.git
```

Then install from **Apps** → search "CRM Pro".

---

## How It Works

### Chatter Resizer

Patches `FormRenderer` to inject a drag handle between the form sheet and chatter panel. The handle listens for mouse events and adjusts the `flex` ratio of both panels. The ratio is persisted in `localStorage` so it survives page reloads.

```
FormRenderer.setup()
  → onMounted / onPatched
    → installResizer()
      → creates drag handle element
      → mousedown → track mousemove → apply flex ratio
      → mouseup → save to localStorage
```

### Email Preview & Last Contact

Two computed fields on `crm.lead`:

| Field | Type | Stored | Source |
|-------|------|--------|--------|
| `x_email_preview` | Char | No | Latest `mail.message` with `type=email` |
| `x_last_message_date` | Datetime | Yes | Latest `mail.message` with `type=email` or `comment` |

Both are displayed in inherited kanban and list views via XPath injection before `tag_ids`.

---

## File Structure

```
pan_crm_pro/
├── __manifest__.py
├── __init__.py
├── models/
│   └── crm_lead.py                 # Email preview + last contact fields
├── views/
│   └── crm_lead_views.xml          # Kanban + list view inheritance
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       ├── js/
│       │   ├── chatter_resizer.js   # Drag-to-resize form/chatter
│       │   └── timeago_field.js     # "3 days ago" OWL widget
│       ├── xml/
│       │   └── timeago_field.xml    # Widget template
│       └── scss/
│           └── chatter_width.scss   # Drag handle styling
└── README.md
```

---

## Contributing

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/pantalytics/pan_crm_pro).

---

## License

[LGPL-3](LICENSE) — Built by [Pantalytics](https://github.com/pantalytics), Odoo implementation partner.
