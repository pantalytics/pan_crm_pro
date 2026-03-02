# -*- coding: utf-8 -*-
"""Extend crm.lead with AI enrichment and CRM UX enhancements."""
import json
import logging
import re
import time

import requests
from lxml import html as lxml_html

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'
ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001'
MAX_EMAIL_CHARS = 3000
MAX_WEBSITE_CHARS = 2000
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 529}

EXTRACTION_PROMPT = """\
You are a contact information extraction assistant. Extract contact details \
from the email content below. Focus on email signatures and footers.

Sender email address: {email_from}
Sender name (if known): {contact_name}

Extract these fields:
- company_name: Company or organization name
- phone: Phone number (landline)
- mobile: Mobile phone number
- contact_name: Full name of the contact
- function: Job title / function
- website: Company website URL (without mailto: or email links)
- street: Street address
- city: City
- zip: Postal / ZIP code
- country: Country name

Return ONLY a JSON object with these keys. Use null for any field you cannot \
confidently extract. Do not guess or infer — only extract what is clearly present.

Email content:
{email_text}\
"""

WEBSITE_PROMPT = """\
Extract company information from this website text.

Return ONLY a JSON object with these keys:
- description: A short company description (max 200 chars)
- industry: The industry or sector this company operates in

Use null for any field you cannot determine.

Website text:
{website_text}\
"""


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # =========================================================================
    # FIELDS
    # =========================================================================

    x_ai_enrich_done = fields.Boolean(
        string='AI Enrichment Done',
        help='Whether AI enrichment from chatter emails has been performed.',
        default=False,
    )
    x_show_ai_enrich_button = fields.Boolean(
        string='Show AI Enrich Button',
        compute='_compute_x_show_ai_enrich_button',
    )
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

    @api.depends('active', 'probability', 'x_ai_enrich_done')
    def _compute_x_show_ai_enrich_button(self):
        """Show Enrich with AI button on active, non-won, non-enriched leads."""
        for lead in self:
            if not lead.active or lead.x_ai_enrich_done or lead.probability == 100:
                lead.x_show_ai_enrich_button = False
            else:
                lead.x_show_ai_enrich_button = True

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

    # =========================================================================
    # ACTION METHODS
    # =========================================================================

    def action_enrich_with_ai(self):
        """Button action: read chatter emails, extract contact data via AI, fill empty fields."""
        self.ensure_one()

        # 1. Get email messages from chatter
        messages = self.env['mail.message'].search([
            ('model', '=', 'crm.lead'),
            ('res_id', '=', self.id),
            ('message_type', '=', 'email'),
        ], order='date desc', limit=10)

        if not messages:
            raise UserError(_('No emails found in the chatter of this lead.'))

        # 2. Extract plain text from email bodies
        email_text = self._enrich_extract_text(messages)

        if not email_text.strip():
            raise UserError(_('No usable email text found in the chatter messages.'))

        # 3. Get API key
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'pan_crm_enrichment.api_key'
        )
        if not api_key:
            raise UserError(_(
                'Anthropic API key not configured. '
                'Go to CRM > Configuration > Settings > AI Enrichment.'
            ))

        # 4. Call Claude API for extraction
        extracted = self._enrich_call_ai(api_key, email_text)

        # 5. Smart merge: only fill empty fields
        updated_fields = self._enrich_apply_lead(extracted)

        # 6. Update linked partner if exists
        if self.partner_id:
            updated_fields += self._enrich_apply_partner(extracted)

        # 7. Optional: website scrape
        website_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'pan_crm_enrichment.website_enabled'
        )
        discovered_website = extracted.get('website') or self.website
        if website_enabled and discovered_website:
            company_data = self._enrich_scrape_website(api_key, discovered_website)
            if company_data:
                updated_fields += self._enrich_apply_company(company_data, discovered_website)

        # 8. Mark enrichment as done
        self.write({'x_ai_enrich_done': True})

        # 9. Post result to chatter and show notification
        if updated_fields:
            msg = _('AI Enrichment updated: %s') % ', '.join(updated_fields)
            self.message_post(body=msg, message_type='notification')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('AI Enrichment'),
                    'message': _('%d field(s) updated.') % len(updated_fields),
                    'type': 'success',
                    'sticky': False,
                },
            }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('AI Enrichment'),
                'message': _('All fields are already filled — nothing to update.'),
                'type': 'warning',
                'sticky': False,
            },
        }

    # =========================================================================
    # LEAD MERGE SUPPORT
    # =========================================================================

    def _merge_get_fields_specific(self):
        """Keep x_ai_enrich_done=True if any merged lead was enriched."""
        res = super()._merge_get_fields_specific()
        res['x_ai_enrich_done'] = lambda fname, leads: any(
            lead.x_ai_enrich_done for lead in leads
        )
        return res

    # =========================================================================
    # TEXT EXTRACTION
    # =========================================================================

    def _enrich_extract_text(self, messages):
        """Convert mail.message HTML bodies to plain text, concatenated."""
        texts = []
        for msg in messages:
            if not msg.body:
                continue
            try:
                doc = lxml_html.document_fromstring(msg.body)
                text = doc.text_content().strip()
            except Exception:
                text = re.sub(r'<[^>]+>', ' ', msg.body).strip()
            if text:
                texts.append(text)
        combined = '\n\n---\n\n'.join(texts)
        return combined[:MAX_EMAIL_CHARS]

    # =========================================================================
    # AI API CALLS
    # =========================================================================

    def _enrich_call_ai(self, api_key, email_text):
        """Call Claude Haiku API for structured contact extraction."""
        prompt = EXTRACTION_PROMPT.format(
            email_from=self.email_from or '',
            contact_name=self.contact_name or '',
            email_text=email_text,
        )
        result = self._enrich_api_request(api_key, prompt)
        return self._enrich_parse_json(result)

    def _enrich_api_request(self, api_key, prompt):
        """Send request to Anthropic API with retry logic for transient errors."""
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        }
        payload = {
            'model': ANTHROPIC_MODEL,
            'max_tokens': 1024,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        last_exception = None
        backoff = INITIAL_BACKOFF_SECONDS

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.post(
                    ANTHROPIC_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                # Retry on transient errors
                if response.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                    retry_after = response.headers.get('retry-after')
                    wait_time = int(retry_after) if retry_after else backoff
                    _logger.warning(
                        f'[AI Enrichment] API returned {response.status_code}, '
                        f'retrying in {wait_time}s ({attempt + 1}/{MAX_RETRIES})'
                    )
                    time.sleep(wait_time)
                    backoff *= 2
                    continue

                response.raise_for_status()
                data = response.json()
                return data['content'][0]['text']

            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < MAX_RETRIES:
                    _logger.warning(
                        f'[AI Enrichment] Request timeout, retrying in {backoff}s '
                        f'({attempt + 1}/{MAX_RETRIES})'
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < MAX_RETRIES:
                    _logger.warning(
                        f'[AI Enrichment] Connection error, retrying in {backoff}s '
                        f'({attempt + 1}/{MAX_RETRIES})'
                    )
                    time.sleep(backoff)
                    backoff *= 2
                    continue

            except requests.exceptions.RequestException as e:
                error_detail = str(e)
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_json = e.response.json()
                        error_detail = error_json.get('error', {}).get('message', str(e))
                    except (ValueError, KeyError):
                        pass
                _logger.error(f'[AI Enrichment] API call failed: {error_detail}')
                raise UserError(_('AI Enrichment API error: %s') % error_detail)

        # All retries exhausted
        error_detail = str(last_exception) if last_exception else 'Unknown error'
        _logger.error(f'[AI Enrichment] API call failed after {MAX_RETRIES} retries: {error_detail}')
        raise UserError(_('AI Enrichment API error after retries: %s') % error_detail)

    @api.model
    def _enrich_parse_json(self, text):
        """Parse JSON from AI response, handling markdown code blocks."""
        text = text.strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            _logger.error(
                f'[AI Enrichment] Failed to parse AI response as JSON: {e}. '
                f'Raw response (first 200 chars): {text[:200]}'
            )
            raise UserError(_(
                'AI returned an invalid response. Please try again. '
                'Check the server logs for details.'
            ))

    # =========================================================================
    # SMART MERGE — LEAD FIELDS
    # =========================================================================

    def _enrich_apply_lead(self, extracted):
        """Apply extracted data to empty lead fields. Returns list of updated field names."""
        field_map = {
            'phone': 'phone',
            'mobile': 'mobile',
            'website': 'website',
            'contact_name': 'contact_name',
            'function': 'function',
            'street': 'street',
            'city': 'city',
            'zip': 'zip',
        }
        vals = {}
        updated = []

        for ai_key, lead_field in field_map.items():
            value = extracted.get(ai_key)
            if value and not getattr(self, lead_field):
                vals[lead_field] = value
                updated.append(lead_field)

        # Company name → partner_name on lead
        company_name = extracted.get('company_name')
        if company_name and not self.partner_name:
            vals['partner_name'] = company_name
            updated.append('partner_name')

        # Country mapping — exact match first, then partial
        country_name = extracted.get('country')
        if country_name and not self.country_id:
            country = self.env['res.country'].search(
                [('name', '=ilike', country_name)], limit=1
            )
            if not country:
                country = self.env['res.country'].search(
                    [('name', 'ilike', country_name)], limit=1
                )
            if country:
                vals['country_id'] = country.id
                updated.append('country_id')

        if vals:
            self.write(vals)
            _logger.info(
                f'[AI Enrichment] Lead {self.id}: updated {", ".join(updated)}'
            )
        return updated

    # =========================================================================
    # SMART MERGE — PARTNER FIELDS
    # =========================================================================

    def _enrich_apply_partner(self, extracted):
        """Apply extracted data to linked partner's empty fields."""
        partner = self.partner_id
        if not partner:
            return []

        field_map = {
            'phone': 'phone',
            'mobile': 'mobile',
            'website': 'website',
            'function': 'function',
        }
        vals = {}
        updated = []

        for ai_key, partner_field in field_map.items():
            value = extracted.get(ai_key)
            if value and not getattr(partner, partner_field):
                vals[partner_field] = value
                updated.append(f'partner.{partner_field}')

        # Link to parent company
        company_name = extracted.get('company_name')
        if company_name and not partner.parent_id and not partner.is_company:
            company = self._enrich_find_or_create_company(
                company_name, extracted.get('website')
            )
            if company:
                vals['parent_id'] = company.id
                updated.append('partner.parent_id')

        if vals:
            partner.write(vals)
            _logger.info(
                f'[AI Enrichment] Partner {partner.id}: updated {", ".join(updated)}'
            )
        return updated

    # =========================================================================
    # COMPANY DEDUPLICATION
    # =========================================================================

    def _enrich_find_or_create_company(self, company_name, website=None):
        """Find existing company by website/name or create a new one."""
        Partner = self.env['res.partner']

        # Search by website first (most reliable)
        if website:
            company = Partner.search([
                ('is_company', '=', True),
                ('website', 'ilike', website),
            ], limit=1)
            if company:
                return company

        # Search by name
        company = Partner.search([
            ('is_company', '=', True),
            ('name', 'ilike', company_name),
        ], limit=1)
        if company:
            return company

        # Create new company partner
        vals = {'name': company_name, 'is_company': True}
        if website:
            vals['website'] = website
        return Partner.create(vals)

    # =========================================================================
    # WEBSITE SCRAPING & COMPANY ENRICHMENT
    # =========================================================================

    def _enrich_scrape_website(self, api_key, url):
        """Scrape website homepage and extract company info via AI."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            response = requests.get(
                url,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; OdooBot/1.0)'},
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.warning(f'[AI Enrichment] Failed to scrape {url}: {e}')
            return None

        try:
            doc = lxml_html.document_fromstring(response.text)
            website_text = doc.text_content().strip()[:MAX_WEBSITE_CHARS]
        except Exception:
            _logger.warning(f'[AI Enrichment] Failed to parse HTML from {url}')
            return None

        if not website_text:
            return None

        prompt = WEBSITE_PROMPT.format(website_text=website_text)
        result = self._enrich_api_request(api_key, prompt)
        return self._enrich_parse_json(result)

    def _enrich_apply_company(self, company_data, website):
        """Apply scraped company data to the partner or lead company."""
        updated = []
        partner = self.partner_id

        # Determine target company partner
        company_partner = None
        if partner and partner.parent_id:
            company_partner = partner.parent_id
        elif partner and partner.is_company:
            company_partner = partner

        if not company_partner:
            return updated

        # Description → comment
        description = company_data.get('description')
        if description and not company_partner.comment:
            company_partner.write({'comment': description})
            updated.append('company.comment')

        # Industry mapping
        industry_name = company_data.get('industry')
        if industry_name and not company_partner.industry_id:
            industry = self.env['res.partner.industry'].search(
                [('name', 'ilike', industry_name)], limit=1
            )
            if industry:
                company_partner.write({'industry_id': industry.id})
                updated.append('company.industry_id')

        if updated:
            _logger.info(
                f'[AI Enrichment] Company {company_partner.id}: '
                f'updated {", ".join(updated)}'
            )
        return updated
