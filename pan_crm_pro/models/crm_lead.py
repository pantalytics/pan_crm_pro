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
    x_recommended_next_step = fields.Text(
        string='Recommended Next Step',
    )
    x_summary = fields.Text(
        string='Summary',
    )
    x_messages_context = fields.Html(
        string='Messages Context',
        compute='_compute_messages_context',
        store=True,
        sanitize=False,
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
                ('message_type', 'in', ('email', 'comment', 'notification')),
            ], order='date desc', limit=1)
            lead.x_last_message_date = last_msg.date if last_msg else False

    @api.depends('message_ids')
    def _compute_messages_context(self):
        """Aggregate the last 100 messages as HTML for AI consumption."""
        for lead in self:
            # Use _origin.id to handle NewId records (e.g. from AI field context)
            rec_id = lead._origin.id if hasattr(lead, '_origin') and lead._origin else lead.id
            if not rec_id or not isinstance(rec_id, int):
                lead.x_messages_context = False
                continue
            messages = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', rec_id),
                ('message_type', 'in', ('email', 'comment', 'notification')),
            ], order='date desc', limit=100)
            parts = []
            for msg in messages:
                date = msg.date.strftime('%Y-%m-%d %H:%M') if msg.date else ''
                author = msg.author_id.name or msg.email_from or ''
                subject = f'<strong>{msg.subject}</strong>' if msg.subject else ''
                header = f'<div><em>[{date}] {author}</em></div>'
                parts.append(f'{header}{subject}{msg.body or ""}')
            lead.x_messages_context = '<hr/>'.join(parts) if parts else False

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
