# -*- coding: utf-8 -*-
"""Extend crm.lead with CRM UX enhancements."""
from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # =========================================================================
    # FIELDS
    # =========================================================================

    x_last_message_date = fields.Datetime(
        string='Last Message',
        compute='_compute_last_message_date',
        store=True,
    )
    x_email_preview = fields.Char(
        string='Email Preview',
        compute='_compute_email_preview',
    )

    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================

    @api.depends('message_ids')
    def _compute_last_message_date(self):
        """Compute date of last email or comment message on the lead."""
        for lead in self:
            last_msg = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('message_type', 'in', ('email', 'comment')),
            ], order='date desc', limit=1)
            lead.x_last_message_date = last_msg.date if last_msg else False

    def _compute_email_preview(self):
        """Compute preview text of the latest email message per lead."""
        messages = self.env['mail.message'].search([
            ('model', '=', 'crm.lead'),
            ('res_id', 'in', self.ids),
            ('message_type', '=', 'email'),
        ], order='id desc')
        preview_map = {}
        for msg in messages:
            if msg.res_id not in preview_map:
                preview_map[msg.res_id] = msg.preview
        for lead in self:
            lead.x_email_preview = preview_map.get(lead.id, False)
