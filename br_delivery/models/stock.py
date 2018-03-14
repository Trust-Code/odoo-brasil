# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    vehicle_id = fields.Many2one(
        'br_delivery.carrier.vehicle', u'Veículo')
    incoterm = fields.Many2one(
        'stock.incoterms', 'Tipo do Frete',
        help="Incoterm which stands for 'International Commercial terms"
        "implies its a series of sales terms which are used in the "
        "commercial transaction.")


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['vehicle_id'] = self.sale_line_id.order_id.vehicle_id.id
        vals['incoterm'] = self.sale_line_id.order_id.incoterm.id
        return vals


class Incoterms(models.Model):
    _inherit = "stock.incoterms"

    freight_responsibility = fields.Selection(
        [('0', u'0 - Emitente'),
         ('1', u'1 - Destinatário'),
         ('2', u'2 - Terceiros'),
         ('9', u'9 - Sem Frete')],
        'Modalidade do frete', default="9")
