# -*- coding: utf-8 -*-
"""Tests for AI enrichment of CRM leads."""
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('pan_crm_pro', 'post_install', '-at_install')
class TestCrmLeadAIEnrich(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lead = cls.env['crm.lead'].create({
            'name': 'Test Lead AI Enrich',
            'email_from': 'john@example.com',
            'type': 'lead',
        })

    # -----------------------------------------------------------------
    # Test: JSON parsing
    # -----------------------------------------------------------------

    def test_enrich_parse_json_valid(self):
        """Valid JSON string is parsed correctly."""
        result = self.lead._enrich_parse_json(
            '{"phone": "+31123456789", "city": "Amsterdam"}'
        )
        self.assertEqual(result['phone'], '+31123456789')
        self.assertEqual(result['city'], 'Amsterdam')

    def test_enrich_parse_json_markdown_fenced(self):
        """JSON wrapped in markdown code fences is parsed correctly."""
        text = '```json\n{"phone": "+31123456789"}\n```'
        result = self.lead._enrich_parse_json(text)
        self.assertEqual(result['phone'], '+31123456789')

    def test_enrich_parse_json_invalid(self):
        """Invalid JSON raises UserError."""
        with self.assertRaises(UserError):
            self.lead._enrich_parse_json('this is not json')

    # -----------------------------------------------------------------
    # Test: Smart merge on lead fields
    # -----------------------------------------------------------------

    def test_enrich_apply_lead_fills_empty(self):
        """AI-extracted data fills empty fields on the lead."""
        self.lead.write({'phone': False, 'city': False, 'partner_name': False})
        extracted = {
            'phone': '+31123456789',
            'city': 'Amsterdam',
            'company_name': 'Acme BV',
        }
        updated = self.lead._enrich_apply_lead(extracted)
        self.assertIn('phone', updated)
        self.assertIn('city', updated)
        self.assertIn('partner_name', updated)
        self.assertEqual(self.lead.phone, '+31123456789')
        self.assertEqual(self.lead.city, 'Amsterdam')
        self.assertEqual(self.lead.partner_name, 'Acme BV')

    def test_enrich_apply_lead_skips_filled(self):
        """AI-extracted data does NOT overwrite existing field values."""
        self.lead.write({'phone': '+31999999999', 'city': 'Rotterdam'})
        extracted = {
            'phone': '+31123456789',
            'city': 'Amsterdam',
        }
        updated = self.lead._enrich_apply_lead(extracted)
        self.assertNotIn('phone', updated)
        self.assertNotIn('city', updated)
        self.assertEqual(self.lead.phone, '+31999999999')
        self.assertEqual(self.lead.city, 'Rotterdam')

    def test_enrich_apply_lead_country_exact_match(self):
        """Country mapping prefers exact match over partial match."""
        self.lead.write({'country_id': False})
        extracted = {'country': 'Netherlands'}
        updated = self.lead._enrich_apply_lead(extracted)
        self.assertIn('country_id', updated)
        self.assertEqual(self.lead.country_id.code, 'NL')

    # -----------------------------------------------------------------
    # Test: Button visibility
    # -----------------------------------------------------------------

    def test_show_button_active_lead(self):
        """Button is visible on an active, non-enriched lead."""
        self.lead.write({'x_ai_enrich_done': False, 'probability': 10})
        self.lead.invalidate_recordset()
        self.assertTrue(self.lead.x_show_ai_enrich_button)

    def test_hide_button_after_enrichment(self):
        """Button is hidden after AI enrichment has been performed."""
        self.lead.write({'x_ai_enrich_done': True})
        self.lead.invalidate_recordset()
        self.assertFalse(self.lead.x_show_ai_enrich_button)
