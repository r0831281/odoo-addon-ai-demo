import logging
import re
from datetime import date, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CrmLeadAI(models.Model):
    _inherit = 'crm.lead'

    # ── AI-enabled fields ────────────────────────────────────────────────────
    x_customer_risk_assessment = fields.Text(
        string='Customer Risk Assessment',
        help=(
            'AI-generated risk assessment based on payment history, '
            'cancelled orders, and financial, strategic or logistics risk indicators. '
            'Populated by the Demo Agent when the user requests a risk assessment.'
        ),
    )
    x_customer_messages_sentiment = fields.Text(
        string='Customer Communication Sentiment',
        help=(
            'AI-generated sentiment analysis across all customer communications. '
            'Identifies overall tone, per-message emotional labels, and outliers '
            '(e.g. angry, frustrated, happy). '
            'Populated by the Demo Agent on request.'
        ),
    )

    # ── Write-back methods called by the AI tools ─────────────────────────────

    def _ai_save_risk_assessment(self, assessment):
        """Persist the AI-generated risk assessment onto the lead record."""
        self.ensure_one()
        self.sudo().write({'x_customer_risk_assessment': assessment})
        return "Customer risk assessment saved to the lead record."

    def _ai_save_messages_sentiment(self, sentiment_summary):
        """Persist the AI-generated sentiment analysis onto the lead record."""
        self.ensure_one()
        self.sudo().write({'x_customer_messages_sentiment': sentiment_summary})
        return "Communication sentiment analysis saved to the lead record."

    # ── Data-read methods called by AI tools ─────────────────────────────────

    def _ai_get_open_invoices(self):
        """Return open/unpaid invoices for the lead's partner."""
        self.ensure_one()
        if not self.partner_id:
            return "No partner linked to this lead."
        invoices = self.env['account.move'].sudo().search([
            ('partner_id', 'child_of', self.partner_id.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
        ])
        if not invoices:
            return "No open invoices found for this customer."
        lines = []
        for inv in invoices:
            lines.append(
                f"- {inv.name} | Due: {inv.invoice_date_due} | "
                f"Outstanding: {inv.amount_residual} {inv.currency_id.name}"
            )
        return "Open invoices:\n" + "\n".join(lines)

    def _ai_get_late_payments(self):
        """Return overdue invoice amounts and number of days overdue."""
        self.ensure_one()
        if not self.partner_id:
            return "No partner linked to this lead."
        today = date.today()
        overdue = self.env['account.move'].sudo().search([
            ('partner_id', 'child_of', self.partner_id.id),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('invoice_date_due', '<', fields.Date.to_string(today)),
        ])
        if not overdue:
            return "No overdue payments found."
        lines = []
        for inv in overdue:
            days = (today - inv.invoice_date_due).days
            lines.append(
                f"- {inv.name} | Overdue by: {days} days | "
                f"Amount: {inv.amount_residual} {inv.currency_id.name}"
            )
        return "Late payments:\n" + "\n".join(lines)

    def _ai_get_open_backorders(self):
        """Return open backorders with product details for the lead's partner."""
        self.ensure_one()
        if not self.partner_id:
            return "No partner linked to this lead."
        pickings = self.env['stock.picking'].sudo().search([
            ('partner_id', 'child_of', self.partner_id.id),
            ('state', 'in', ('waiting', 'confirmed', 'assigned')),
            ('backorder_id', '!=', False),
        ])
        if not pickings:
            return "No open backorders found for this customer."
        lines = []
        for pick in pickings:
            products = []
            for move in pick.move_ids:
                # Odoo 17+ uses `quantity`; earlier versions use `quantity_done`
                qty_done = getattr(move, 'quantity', None)
                if qty_done is None:
                    qty_done = getattr(move, 'quantity_done', 0)
                products.append(
                    f"{move.product_id.display_name} "
                    f"(ordered: {move.product_uom_qty}, done: {qty_done})"
                )
            lines.append(
                f"- {pick.name} | Scheduled: {pick.scheduled_date} | "
                f"Products: {', '.join(products)}"
            )
        return "Open backorders:\n" + "\n".join(lines)

    def _ai_get_communication(self, limit=20):
        """Return recent chatter messages, emails, notes and voice transcriptions."""
        self.ensure_one()
        effective_limit = int(limit) if limit else 20
        messages = self.env['mail.message'].sudo().search([
            ('res_id', '=', self.id),
            ('model', '=', 'crm.lead'),
            ('message_type', 'in', ('email', 'comment', 'email_outgoing')),
        ], order='date desc', limit=effective_limit)
        if not messages:
            return "No communication found on this lead."
        lines = []
        for msg in messages:
            author = msg.author_id.display_name or 'Unknown'
            date_str = msg.date.strftime('%Y-%m-%d %H:%M') if msg.date else ''
            body = re.sub(r'<[^>]+>', ' ', (msg.body or '')).strip()
            body = (body[:300] + '…') if len(body) > 300 else body
            lines.append(f"[{date_str}] {author}: {body}")
        return "Recent communication:\n" + "\n".join(lines)

    def _ai_get_logistics_issues(self):
        """Return overdue deliveries / logistics problems for the lead's partner."""
        self.ensure_one()
        if not self.partner_id:
            return "No partner linked to this lead."
        now = fields.Datetime.now()
        pickings = self.env['stock.picking'].sudo().search([
            ('partner_id', 'child_of', self.partner_id.id),
            ('state', 'in', ('waiting', 'confirmed', 'assigned')),
            ('scheduled_date', '<', now),
        ])
        if not pickings:
            return "No overdue deliveries found."
        lines = []
        for pick in pickings:
            products = [m.product_id.display_name for m in pick.move_ids]
            lines.append(
                f"- {pick.name} | Type: {pick.picking_type_id.name} | "
                f"Scheduled: {pick.scheduled_date} | "
                f"Products: {', '.join(products)}"
            )
        return "Logistics issues (overdue pickings):\n" + "\n".join(lines)

    @api.model
    def _ai_create_demo_lead(self, name, description, partner_id=None, team_id=None):
        """Create a new CRM lead/opportunity and return a success message."""
        vals = {
            'name': name,
            'description': description or '',
        }
        if partner_id:
            vals['partner_id'] = int(partner_id)
        if team_id:
            vals['team_id'] = int(team_id)
        lead = self.sudo().create(vals)
        return f"Success: Lead #{lead.id} '{lead.name}' created."

    # ── Demo data generator ───────────────────────────────────────────────────

    @api.model
    def _ai_demo_create_context_data(self, partner_id, lead_id, template_ids):
        """Create rich contextual demo data for the AI Demo addon.

        Creates two confirmed historical sale orders and two posted invoices
        (one overdue, one upcoming) for the demo partner so that all AI tools
        return meaningful results out-of-the-box.

        Called from demo/demo_data.xml via <function>.
        Safe to call multiple times — skips silently if demo data already exists.
        """
        partner = self.env['res.partner'].browse(partner_id)
        templates = self.env['product.template'].browse(template_ids)
        variants = templates.mapped('product_variant_ids')

        if not partner.exists() or not variants:
            return True

        today = date.today()
        v = variants  # shorthand for readability

        # ── Guard: skip if already created ───────────────────────────────────
        if self.env['sale.order'].sudo().search(
            [('partner_id', '=', partner.id), ('client_order_ref', '=', 'AI-DEMO')],
            limit=1,
        ):
            return True

        def _variant(idx):
            """Return variant at index, falling back to first variant."""
            return v[idx] if len(v) > idx else v[0]

        # ── Sale Order 1: Q4 2024 – laptops + docking stations ───────────────
        order1 = self.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'client_order_ref': 'AI-DEMO',
            'date_order': (today - timedelta(days=180)).strftime('%Y-%m-%d %H:%M:%S'),
            'note': 'Annual hardware refresh – batch 1 (20 workstations)',
            'order_line': [
                (0, 0, {
                    'product_id': _variant(0).id,
                    'product_uom_qty': 20,
                    'price_unit': 1299.00,
                    'name': _variant(0).display_name,
                }),
                (0, 0, {
                    'product_id': _variant(1).id,
                    'product_uom_qty': 20,
                    'price_unit': 249.00,
                    'name': _variant(1).display_name,
                }),
            ],
        })
        try:
            order1.action_confirm()
        except Exception:
            _logger.warning('AI Demo: could not confirm demo sale order 1 (left in draft).')

        # ── Sale Order 2: Q1 2025 – headsets top-up ──────────────────────────
        order2 = self.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'client_order_ref': 'AI-DEMO',
            'date_order': (today - timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S'),
            'note': 'Accessories top-up – noise-cancelling headsets',
            'order_line': [
                (0, 0, {
                    'product_id': _variant(2).id,
                    'product_uom_qty': 15,
                    'price_unit': 189.00,
                    'name': _variant(2).display_name,
                }),
            ],
        })
        try:
            order2.action_confirm()
        except Exception:
            _logger.warning('AI Demo: could not confirm demo sale order 2 (left in draft).')

        # ── Invoice 1: Overdue (issued 60 days ago, 30 days past due) ─────────
        try:
            inv1 = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date': (today - timedelta(days=60)).strftime('%Y-%m-%d'),
                'invoice_date_due': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
                'ref': 'AI-DEMO-INV-001',
                'invoice_line_ids': [(0, 0, {
                    'product_id': _variant(0).id,
                    'quantity': 20,
                    'price_unit': 1299.00,
                    'name': _variant(0).display_name,
                })],
            })
            inv1.action_post()
        except Exception:
            _logger.warning(
                'AI Demo: could not create/post demo invoice 1. '
                'Install a chart of accounts so invoice AI tools return data.'
            )

        # ── Invoice 2: Recent unpaid (issued 5 days ago, due in 25 days) ──────
        try:
            inv2 = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': partner.id,
                'invoice_date': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
                'invoice_date_due': (today + timedelta(days=25)).strftime('%Y-%m-%d'),
                'ref': 'AI-DEMO-INV-002',
                'invoice_line_ids': [(0, 0, {
                    'product_id': _variant(2).id,
                    'quantity': 15,
                    'price_unit': 189.00,
                    'name': _variant(2).display_name,
                })],
            })
            inv2.action_post()
        except Exception:
            _logger.warning('AI Demo: could not create/post demo invoice 2.')

        return True
