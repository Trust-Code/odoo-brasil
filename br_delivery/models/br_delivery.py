# -*- coding: utf-8 -*-
# © 2010  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class BrDeliveryCarrierVehicle(models.Model):
    _name = 'br_delivery.carrier.vehicle'
    _description = u'Veículos das transportadoras'

    name = fields.Char(u'Nome', required=True, size=32)
    description = fields.Char(u'Descrição', size=132)
    plate = fields.Char(u'Placa', size=7)
    driver = fields.Char(u'Condutor', size=64)
    rntc_code = fields.Char(u'Código ANTT', size=32)
    country_id = fields.Many2one('res.country', u'País')
    state_id = fields.Many2one(
        'res.country.state', u'Estado',
        domain="[('country_id', '=', country_id)]")
    city_id = fields.Many2one(
        'res.state.city', u'Município',
        domain="[('state_id','=',state_id)]")
    active = fields.Boolean(u'Ativo')
    manufacture_year = fields.Char(u'Ano de Fabricação', size=4)
    model_year = fields.Char(u'Ano do Modelo', size=4)
    type = fields.Selection([('bau', u'Caminhão Baú')], u'Tipo')
    carrier_id = fields.Many2one(
        'delivery.carrier', u'Carrier', index=True,
        required=True, ondelete='cascade')
