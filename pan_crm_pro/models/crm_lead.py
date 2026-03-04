# -*- coding: utf-8 -*-
"""Extend crm.lead with CRM UX enhancements."""
import html
import re

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
    x_messages_context = fields.Text(
        string='Messages Context',
        compute='_compute_messages_context',
        help='Recent messages as plain text for use as AI field context.',
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

    @api.depends('message_ids')
    def _compute_messages_context(self):
        """Build plain-text digest of recent messages for AI field context."""
        TAG_RE = re.compile(r'<[^>]+>')
        for lead in self:
            messages = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('message_type', 'in', ('email', 'comment')),
            ], order='date desc', limit=20)
            parts = []
            for msg in messages:
                body_plain = html.unescape(TAG_RE.sub('', msg.body or ''))
                body_plain = re.sub(r'\n{3,}', '\n\n', body_plain).strip()
                if not body_plain:
                    continue
                header = f"From: {msg.author_id.name or msg.email_from or 'Unknown'}"
                if msg.date:
                    header += f" | Date: {msg.date.strftime('%Y-%m-%d %H:%M')}"
                if msg.subject:
                    header += f" | Subject: {msg.subject}"
                parts.append(f"{header}\n{body_plain}")
            lead.x_messages_context = '\n---\n'.join(parts) if parts else False

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
