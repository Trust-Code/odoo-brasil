# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2010  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from odoo import fields, models


class L10n_brDeliveryCarrierVehicle(models.Model):
    _name = 'l10n_br_delivery.carrier.vehicle'
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
        'delivery.carrier', u'Carrier', select=True,
        required=True, ondelete='cascade')


class L10n_brDeliveryShipment(models.Model):
    _name = 'l10n_br_delivery.shipment'

    code = fields.Char(u'Nome', size=32)
    description = fields.Char(u'Descrição', size=132)
    carrier_id = fields.Many2one(
        'delivery.carrier', u'Carrier', select=True, required=True)
    vehicle_id = fields.Many2one(
        'l10n_br_delivery.carrier.vehicle', u'Vehicle', select=True,
        required=True)
    volume = fields.Float(u'Volume')
    carrier_tracking_ref = fields.Char(u'Carrier Tracking Ref', size=32)
    number_of_packages = fields.Integer(u'Number of Packages')

    #@api.depends('product_id', 'move_lines') # TODO Esta função deveria estar aqui?
    def _cal_weight(self):
        for picking in self:
            picking.weight = sum(move.weight for move in picking.move_lines if move.state != 'cancel')
            picking.weight = sum(move.weight_net for move in picking.move_lines if move.state != 'cancel')
