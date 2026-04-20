import re
from datetime import date

from odoo import api, fields, models


class CrmLeadAI(models.Model):
    _inherit = 'crm.lead'

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
