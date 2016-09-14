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
