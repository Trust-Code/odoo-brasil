# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class L10nBrWebsiteSale(main.WebsiteSale):

    mandatory_billing_fields = ["name", "phone", "email", "cnpj_cpf", "zip",
                                "street", "number", "district", "country_id",
                                "state_id", "city_id"]
    mandatory_shipping_fields = ["name", "phone", "zip",
                                 "street", "number", "district", "country_id",
                                 "state_id", "city_id"]

    @http.route(['/shop/get_cities'], type='json', auth="public",
                methods=['POST'], website=True)
    def get_cities_json(self, state_id):
        if state_id.isdigit():
            cities = request.env['res.state.city'].sudo().search(
                [('state_id', '=', int(state_id))])
            return [(city.id, city.name) for city in cities]
        return []

    def checkout_parse(self, address_type, data, remove_prefix=False):
        val = super(L10nBrWebsiteSale, self).checkout_parse(
            address_type, data, remove_prefix)
        if address_type == 'billing':
            val['cnpj_cpf'] = data['cnpj_cpf']
            val['number'] = data['number']
            val['district'] = data['district']
            val['street2'] = data['street2']
            val['zip'] = data['zip']
            val['city_id'] = data['city_id']
        if address_type == 'shipping':
            val['shipping_cnpj_cpf'] = data['cnpj_cpf']
            val['shipping_number'] = data['number']
            val['shipping_district'] = data['district']
            val['shipping_street2'] = data['street2']
            val['shipping_zip'] = data['zip']
            val['shipping_city_id'] = data['city_id']
        return val

    def checkout_form_validate(self, data):
        error = super(L10nBrWebsiteSale, self).checkout_form_validate(data)
        return error
