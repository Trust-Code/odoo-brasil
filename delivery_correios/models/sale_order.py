# © 2020 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_type = fields.Selection(related="carrier_id.delivery_type",
                                     string=u"Tipo integração")
    service_id = fields.Many2one(
        'delivery.correios.service', string=u"Serviço",
        domain="[('delivery_id', '=', carrier_id)]")
