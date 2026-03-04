# -*- coding: utf-8 -*-
{
    'name': 'CRM Pro',
    'summary': 'CRM productivity enhancements: chatter resizer, email preview, last contact',
    'description': """
CRM Pro
=======

Productivity enhancements for Odoo CRM by Pantalytics.

**Chatter Resizer** — Drag the boundary between the form and chatter to resize.

**Email Preview** — See the latest email preview in kanban and list views.

**Last Contact** — Relative timestamp ("3 days ago") of the last message.
    """,
    'author': 'Pantalytics B.V. by Rutger Hofste',
    'website': 'https://www.pantalytics.com/',
    'support': 'support@pantalytics.com',
    'category': 'CRM',
    'version': '19.0.2.0.0',
    'license': 'LGPL-3',
    'depends': ['crm', 'mail', 'pan_ai_pro'],
    'data': [
        'views/crm_lead_views.xml',
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
