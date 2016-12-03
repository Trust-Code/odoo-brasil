# -*- coding: utf-8 -*-
# © 2010  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    carrier_id = fields.Many2one(
        'delivery.carrier', 'Transportadora', readonly=True,
        states={'draft': [('readonly', False)]})
    vehicle_id = fields.Many2one(
        'br_delivery.carrier.vehicle', u'Veículo', readonly=True,
        states={'draft': [('readonly', False)]})
    incoterm = fields.Many2one('stock.incoterms', 'Tipo do Frete',
                               readonly=True,
                               states={'draft': [('readonly', False)]},
                               help="Incoterm which stands for 'International "
                                    "Commercial terms' implies its a series "
                                    "of sales terms which are used in the "
                                    "commercial transaction.")
