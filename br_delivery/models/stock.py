# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    vehicle_id = fields.Many2one(
        'br_delivery.carrier.vehicle', u'Veículo')
    incoterm = fields.Many2one(
        'stock.incoterms', 'Tipo do Frete',
        help="Incoterm which stands for 'International Commercial terms"
        "implies its a series of sales terms which are used in the "
        "commercial transaction.")
    carrier_id = fields.Many2one(
        'delivery.carrier', 'Carrier')
    vehicle_plate = fields.Char(u'Placa do Veículo', size=7)
    vehicle_state_id = fields.Many2one('res.country.state', 'UF da Placa')
    vehicle_rntc = fields.Char('RNTC', size=20)
    freight_responsibility = fields.Selection(
        [('0', u'0 - Emitente'),
         ('1', u'1 - Destinatário'),
         ('2', u'2 - Terceiros'),
         ('9', u'9 - Sem Frete')],
        u'Modalidade do frete')

    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        if self.vehicle_id:
            self.vehicle_plate = self.vehicle_id.plate
            self.vehicle_state_id = self.vehicle_id.state_id.id
            self.vehicle_rntc = self.vehicle_id.rntc_code

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        if self.carrier_id:
            self.incoterm = self.carrier_id.incoterm
            self.freight_responsibility = self.incoterm.freight_responsibility

    @api.multi
    def _add_delivery_cost_to_so(self):
        return


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['incoterm'] = self.sale_line_id.order_id.incoterm.id
        vals['carrier_id'] = self.sale_line_id.order_id.carrier_id.id
        vals['freight_responsibility'] =\
            self.sale_line_id.order_id.incoterm.freight_responsibility
        return vals


class Incoterms(models.Model):
    _inherit = "stock.incoterms"

    freight_responsibility = fields.Selection(
        [('0', u'0 - Emitente'),
         ('1', u'1 - Destinatário'),
         ('2', u'2 - Terceiros'),
         ('9', u'9 - Sem Frete')],
        'Modalidade do frete', default="9")
