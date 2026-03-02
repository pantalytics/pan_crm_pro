# -*- coding: utf-8 -*-
{
    'name': 'CRM Pro',
    'summary': 'CRM productivity enhancements: AI enrichment, chatter resizer, email preview',
    'description': """
CRM Pro
=======

Productivity enhancements for Odoo CRM by Pantalytics.

**AI Enrichment** — Enrich leads with contact data extracted from chatter emails
using Claude AI. Smart merge fills only empty fields, never overwrites.

**Chatter Resizer** — Drag the boundary between the form and chatter to resize.

**Email Preview** — See the latest email preview in kanban and list views.

**Last Contact** — Relative timestamp ("3 days ago") of the last message.

**Data Disclosure:** Email content from the lead chatter is sent to the
Anthropic Claude API for contact extraction. No data is stored externally.
    """,
    'author': 'Pantalytics B.V. by Rutger Hofste',
    'website': 'https://www.pantalytics.com/',
    'support': 'support@pantalytics.com',
    'category': 'CRM',
    'version': '19.0.1.3.0',
    'license': 'OPL-1',
    'depends': ['crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pan_crm_pro/static/src/scss/chatter_width.scss',
            'pan_crm_pro/static/src/js/chatter_resizer.js',
            'pan_crm_pro/static/src/js/timeago_field.js',
            'pan_crm_pro/static/src/xml/timeago_field.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
