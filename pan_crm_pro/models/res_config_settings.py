# -*- coding: utf-8 -*-
"""Configuration settings for CRM AI Enrichment."""
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_enrichment_api_key = fields.Char(
        string='Anthropic API Key',
        config_parameter='pan_crm_pro.api_key',
    )
    x_enrichment_website_enabled = fields.Boolean(
        string='Enable Website Scraping',
        config_parameter='pan_crm_pro.website_enabled',
    )
