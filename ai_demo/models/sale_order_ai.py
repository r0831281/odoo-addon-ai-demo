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
        """Return available products with price and available stock.

        Returns product.product (variant) IDs so they can be used directly
        as product_id on sale.order.line without further conversion.
        """
        domain = [('sale_ok', '=', True), ('active', '=', True)]
        if category_id:
            domain.append(('categ_id', '=', int(category_id)))
        templates = self.sudo().search(domain, limit=50)
        if not templates:
            return "No products found."
        lines = []
        for tmpl in templates:
            variant = tmpl.product_variant_ids[:1]
            if not variant:
                continue
            ref = f"[{tmpl.default_code}] " if tmpl.default_code else ""
            lines.append(
                f"- product_id={variant.id} | {ref}{tmpl.name} | "
                f"Price: {tmpl.list_price} {tmpl.currency_id.name} | "
                f"Stock: {tmpl.qty_available}"
            )
        return "Product catalogue:\n" + "\n".join(lines)


class SaleOrderAI(models.Model):
    """Quotation creation method for AI-driven offer generation."""
    _inherit = 'sale.order'

    @api.model
    def _ai_create_quotation(self, partner_id, product_ids=None, quantities=None, prices=None, note=None):
        """Create a draft sale order (quotation) and return its name and id.

        Accepts parallel lists: product_ids (product.product IDs from the
        catalogue tool), quantities, and optional prices (unit prices; falls
        back to the product list price when omitted or zero).
        """
        try:
            partner_id = int(partner_id)
        except (TypeError, ValueError):
            return "Tool error: 'partner_id' must be a valid integer. Make sure the lead has a linked customer, or pass the partner_id explicitly."

        if product_ids is None:
            product_ids = []
        if quantities is None:
            quantities = []
        if prices is None:
            prices = []

        if not isinstance(product_ids, list):
            return "Tool error: 'product_ids' must be a list."
        if not isinstance(quantities, list):
            return "Tool error: 'quantities' must be a list."

        if len(product_ids) != len(quantities):
            return "Tool error: 'product_ids' and 'quantities' must have the same length."

        order_lines = []
        product_model = self.sudo().env['product.product']
        for index, (pid, qty_val) in enumerate(zip(product_ids, quantities), start=1):
            try:
                product_id = int(pid)
            except (TypeError, ValueError):
                return f"Tool error: line {index} has an invalid 'product_id'."

            product = product_model.browse(product_id).exists()
            if not product:
                return f"Tool error: line {index} references unknown product_id {product_id}."

            try:
                qty = float(qty_val)
            except (TypeError, ValueError):
                return f"Tool error: line {index} has an invalid 'qty'."

            try:
                raw_price = prices[index - 1] if index - 1 < len(prices) else None
                price_unit = float(raw_price or 0.0) or product.lst_price
            except (TypeError, ValueError):
                return f"Tool error: line {index} has an invalid 'price_unit'."

            order_lines.append((0, 0, {
                'product_id': product.id,
                'product_uom_qty': qty,
                'price_unit': price_unit,
            }))
        order = self.sudo().create({
            'partner_id': partner_id,
            'order_line': order_lines,
            'note': note or '',
        })
        return f"Quotation {order.name} created (id={order.id})."
