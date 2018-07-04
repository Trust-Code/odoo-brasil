from odoo.addons import decimal_precision as dp
from odoo import models, api, fields

class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    purchase_order_id = fields.Many2one('purchase.order', string='Pedido de Compra')
    partner_product_uom = fields.Char(string=u'Unidade de Medida do Fornecedor')
    partner_product_uom_qty = fields.Float(string=u'Quantidade no Fornecedor',
                                           digits=dp.get_precision('Product Unit of Measure'))

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def _add_supplier_to_product(self):
        # Reescrevendo a função para armazenar o número do pedido que gerou a informação
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if partner not in line.product_id.seller_ids.mapped('name') and len(line.product_id.seller_ids) <= 10:
                currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
                supplierinfo = {
                    'name': partner.id,
                    'sequence': max(
                        line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
                    'product_uom': line.product_uom.id,
                    'purchase_order_id': self.id,
                    'min_qty': 0.0,
                    'price': self.currency_id.compute(line.price_unit, currency),
                    'currency_id': currency.id,
                    'delay': 0,
                }
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError:  # no write access rights -> just ignore
                    break
