# -*- coding: utf-8 -*-
{
    'name': 'CRM AI Enrichment',
    'summary': 'Enrich CRM leads with AI-extracted contact data from chatter emails',
    'description': """
CRM AI Enrichment
=================

Adds an **Enrich with AI** button to the CRM lead form. Reads emails from the
lead chatter, sends the content to the Anthropic Claude API, and fills in
missing contact fields on the lead and/or linked partner.

**Data Disclosure:** Email content from the lead chatter is sent to the
Anthropic Claude API for contact extraction. No data is stored externally.

Key Features
------------
* On-demand enrichment (no cron, no queue)
* Smart merge: only fills empty fields, never overwrites existing data
* Extracts: name, phone, mobile, email, function, company, website, address
* Optional website scraping for company description and industry
* Company deduplication by website and name
* Summary of updated fields posted to chatter
    """,
    'author': 'Pantalytics B.V. by Rutger Hofste',
    'website': 'https://www.pantalytics.com/',
    'support': 'support@pantalytics.com',
    'category': 'CRM',
    'version': '19.0.1.2.0',
    'license': 'OPL-1',
    'depends': ['crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pan_crm_enrichment/static/src/scss/chatter_width.scss',
            'pan_crm_enrichment/static/src/js/chatter_resizer.js',
            'pan_crm_enrichment/static/src/js/timeago_field.js',
            'pan_crm_enrichment/static/src/xml/timeago_field.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
