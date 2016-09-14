# -*- coding: utf-8 -*-
# © 2010  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
###############################################################################


from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    antt_code = fields.Char('Codigo ANTT', size=32)
    vehicle_ids = fields.One2many(
        'l10n_br_delivery.carrier.vehicle', 'carrier_id', u'Veículos')
