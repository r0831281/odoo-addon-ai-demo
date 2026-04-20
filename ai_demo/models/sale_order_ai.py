import re

from odoo import api, models


class CrmLeadSaleAI(models.Model):
    """Sale-history and offer-generation methods on the CRM Lead."""
    _inherit = 'crm.lead'

    def _ai_get_sale_history(self, limit=10):
        """Return confirmed sale order history for the lead's partner."""
        self.ensure_one()
        if not self.partner_id:
            return "No partner linked to this lead."
        orders = self.env['sale.order'].sudo().search([
            ('partner_id', 'child_of', self.partner_id.id),
            ('state', 'in', ('sale', 'done')),
        ], order='date_order desc', limit=int(limit) if limit else 10)
        if not orders:
            return "No confirmed sale orders found for this customer."
        lines = []
        for order in orders:
            products = [
                f"{l.product_id.display_name} x{l.product_uom_qty}"
                for l in order.order_line
            ]
            lines.append(
                f"- {order.name} | {order.date_order.strftime('%Y-%m-%d')} | "
                f"Total: {order.amount_total} {order.currency_id.name} | "
                f"Products: {', '.join(products[:5])}"
            )
        return "Sale history:\n" + "\n".join(lines)

    def _ai_get_sale_messages(self, limit=15):
        """Return relevant messages from this lead and linked sale orders."""
        self.ensure_one()
        effective_limit = int(limit) if limit else 15
        sale_orders = self.env['sale.order'].sudo().search(
            [('partner_id', 'child_of', self.partner_id.id)], limit=5
        ) if self.partner_id else self.env['sale.order']

        if sale_orders:
            domain = [
                '|',
                '&', ('res_id', '=', self.id), ('model', '=', 'crm.lead'),
                '&', ('res_id', 'in', sale_orders.ids), ('model', '=', 'sale.order'),
            ]
        else:
            domain = [('res_id', '=', self.id), ('model', '=', 'crm.lead')]

        messages = self.env['mail.message'].sudo().search(
            domain, order='date desc', limit=effective_limit
        )
        if not messages:
            return "No messages found."
        lines = []
        for msg in messages:
            author = msg.author_id.display_name or 'Unknown'
            date_str = msg.date.strftime('%Y-%m-%d %H:%M') if msg.date else ''
            body = re.sub(r'<[^>]+>', ' ', (msg.body or '')).strip()
            body = (body[:200] + '…') if len(body) > 200 else body
            lines.append(f"[{date_str}] {msg.model}/{msg.res_id} – {author}: {body}")
        return "Messages:\n" + "\n".join(lines)


class ProductTemplateAI(models.Model):
    """Product catalogue read method for AI offer generation."""
    _inherit = 'product.template'

    @api.model
    def _ai_get_product_catalogue(self, category_id=None):
        """Return available products with price and available stock."""
        domain = [('sale_ok', '=', True), ('active', '=', True)]
        if category_id:
            domain.append(('categ_id', '=', int(category_id)))
        products = self.sudo().search(domain, limit=50)
        if not products:
            return "No products found."
        lines = []
        for p in products:
            ref = f"[{p.default_code}] " if p.default_code else ""
            lines.append(
                f"- {ref}{p.name} | "
                f"Price: {p.list_price} {p.currency_id.name} | "
                f"Stock: {p.qty_available}"
            )
        return "Product catalogue:\n" + "\n".join(lines)


class SaleOrderAI(models.Model):
    """Quotation creation method for AI-driven offer generation."""
    _inherit = 'sale.order'

    @api.model
    def _ai_create_quotation(self, partner_id, lines=None, note=None):
        """Create a draft sale order (quotation) and return its name and id."""
        order_lines = []
        for line in (lines or []):
            order_lines.append((0, 0, {
                'product_id': int(line['product_id']),
                'product_uom_qty': float(line.get('qty', 1.0)),
                'price_unit': float(line.get('price_unit', 0.0)),
            }))
        order = self.sudo().create({
            'partner_id': int(partner_id),
            'order_line': order_lines,
            'note': note or '',
        })
        return f"Quotation {order.name} created (id={order.id})."
