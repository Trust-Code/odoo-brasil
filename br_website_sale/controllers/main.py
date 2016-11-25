# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class L10nBrWebsiteSale(main.WebsiteSale):

    def _get_mandatory_billing_fields(self):
        res = super(L10nBrWebsiteSale, self)._get_mandatory_billing_fields()
        res.remove('city')
        return res + ["cnpj_cpf", "zip", "number", "district",
                      "state_id", "city_id"]

    def _get_mandatory_shipping_fields(self):
        res = super(L10nBrWebsiteSale, self)._get_mandatory_shipping_fields()
        res.remove('city')
        return res + ["cnpj_cpf", "zip", "number", "district",
                      "state_id", "city_id"]

    @http.route(['/shop/get_cities'], type='json', auth="public",
                methods=['POST'], website=True)
    def get_cities_json(self, state_id):
        if state_id.isdigit():
            cities = request.env['res.state.city'].sudo().search(
                [('state_id', '=', int(state_id))])
            return [(city.id, city.name) for city in cities]
        return []

    @http.route(['/shop/get_states'], type='json', auth="public",
                methods=['POST'], website=True)
    def get_states_json(self, country_id):
        if country_id.isdigit():
            states = request.env['res.country.state'].sudo().search(
                [('country_id', '=', int(country_id))])
            return [(state.id, state.name) for state in states]
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
            val['company_type'] = data['company_type']
        if address_type == 'shipping':
            val['shipping_cnpj_cpf'] = data['cnpj_cpf']
            val['shipping_number'] = data['number']
            val['shipping_district'] = data['district']
            val['shipping_street2'] = data['street2']
            val['shipping_zip'] = data['zip']
            val['shipping_city_id'] = data['city_id']
            val['company_type'] = data['company_type']
        return val

    def checkout_form_validate(self, mode, all_form_values, data):
        error = super(L10nBrWebsiteSale, self).checkout_form_validate(
            mode, all_form_values, data)
        return error

    @http.route()
    def address(self, **kw):
        result = super(L10nBrWebsiteSale, self).address(**kw)
        partner_id = 0
        if "partner_id" in result.qcontext:
            partner_id = result.qcontext['partner_id']
        if partner_id > 0:
            partner_id = request.env['res.partner'].browse(partner_id)
            result.qcontext['city'] = partner_id.city_id.id
            result.qcontext['state'] = partner_id.state_id.id
        return result

    @http.route(['/shop/zip_search'], type='json', auth="public",
                methods=['POST'], website=True)
    def search_zip_json(self, zip):
        if len(zip) >= 8:
            cep = re.sub('[^0-9]', '', zip)
            zip_ids = request.env['br.zip'].sudo().zip_search_multi(
                zip_code=cep)

            if len(zip_ids) == 1:
                return {'sucesso': True,
                        'street': zip_ids[0].street,
                        'district': zip_ids[0].district,
                        'city_id': zip_ids[0].city_id.id,
                        'state_id': zip_ids[0].state_id.id,
                        'country_id': zip_ids[0].country_id.id}

        return {'sucesso': False}
