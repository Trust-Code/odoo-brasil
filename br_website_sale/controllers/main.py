# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import http
from odoo.http import request
from werkzeug.exceptions import Forbidden
import odoo.addons.website_sale.controllers.main as main
from odoo.addons.br_base.tools.fiscal import validate_cnpj, validate_cpf
from odoo.addons.portal.controllers.portal import CustomerPortal


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
        if state_id and state_id.isdigit():
            cities = request.env['res.state.city'].sudo().search(
                [('state_id', '=', int(state_id))])
            return [(city.id, city.name) for city in cities]
        return []

    @http.route(['/shop/get_states'], type='json', auth="public",
                methods=['POST'], website=True)
    def get_states_json(self, country_id):
        if country_id and country_id.isdigit():
            states = request.env['res.country.state'].sudo().search(
                [('country_id', '=', int(country_id))])
            return [(state.id, state.name) for state in states]
        return []

    def checkout_form_validate(self, mode, all_form_values, data):
        errors, error_msg = super(L10nBrWebsiteSale, self).\
            checkout_form_validate(mode, all_form_values, data)
        cnpj_cpf = data.get('cnpj_cpf', '0')
        email = data.get('email', False)
        if cnpj_cpf and len(cnpj_cpf) == 18:
            if not validate_cnpj(cnpj_cpf):
                errors["cnpj_cpf"] = u"invalid"
                error_msg.append(('CNPJ Inválido!'))
        elif cnpj_cpf and len(cnpj_cpf) == 14:
            if not validate_cpf(cnpj_cpf):
                errors["cnpj_cpf"] = u"invalid"
                error_msg.append(('CPF Inválido!'))
        partner_id = data.get('partner_id', False)
        if cnpj_cpf:
            domain = [('cnpj_cpf', '=', cnpj_cpf)]
            if partner_id and mode[0] == 'edit':
                domain.append(('id', '!=', partner_id))
            existe = request.env["res.partner"].sudo().search_count(domain)
            if existe > 0:
                errors["cnpj_cpf"] = u"invalid"
                error_msg.append(('CPF/CNPJ já cadastrado'))
        if email:
            domain = [('email', '=', email)]
            if partner_id and mode[0] == 'edit':
                domain.append(('id', '!=', partner_id))
            existe = request.env["res.partner"].sudo().search_count(domain)
            if existe > 0:
                errors["email"] = u"invalid"
                error_msg.append(('E-mail já cadastrado'))
        if 'city_id' in data and not data['city_id']:
            errors["city_id"] = u"missing"
            error_msg.append('Selecione uma cidade')
        if 'phone' in data and not data['phone']:
            errors["phone"] = u"missing"
            error_msg.append('Informe o seu número de telefone')
        return errors, error_msg

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super(L10nBrWebsiteSale, self).\
            values_postprocess(order, mode, values, errors, error_msg)
        new_values['cnpj_cpf'] = values.get('cnpj_cpf', None)
        new_values['company_type'] = values.get('company_type', None)
        is_comp = False if values.get('company_type', None) == 'person'\
            else True
        new_values['is_company'] = is_comp
        if 'city_id' in values and values['city_id'] != '':
            new_values['city_id'] = int(values.get('city_id', 0))
        if 'state_id' in values and values['state_id'] != '':
            new_values['state_id'] = int(values.get('state_id', 0))
        if 'country_id' in values and values['country_id'] != '':
            new_values['country_id'] = int(values.get('country_id', 0))
        new_values['number'] = values.get('number', None)
        new_values['street2'] = values.get('street2', None)
        new_values['district'] = values.get('district', None)
        return new_values, errors, error_msg

    def _checkout_form_save(self, mode, checkout, all_values):
        Partner = request.env['res.partner']
        if mode[0] == 'new':
            partner_id = Partner.sudo().create(checkout)
        elif mode[0] == 'edit':
            partner_id = int(all_values.get('partner_id', 0))
            if partner_id:
                # double check
                order = request.website.sale_get_order()
                shippings = Partner.sudo().search(
                    [("id", "child_of",
                      order.partner_id.commercial_partner_id.ids)])
                if partner_id not in shippings.mapped('id') and \
                   partner_id != order.partner_id.id:
                    return Forbidden()

                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id

    @http.route()
    def address(self, **kw):
        result = super(L10nBrWebsiteSale, self).address(**kw)
        partner_id = 0
        if "partner_id" in result.qcontext:
            partner_id = result.qcontext['partner_id']
        if partner_id > 0:
            partner_id = request.env['res.partner'].sudo().browse(partner_id)
            result.qcontext['city'] = partner_id.city_id.id
            result.qcontext['state'] = partner_id.state_id.id
        if 'city_id' in kw and kw['city_id']:
            result.qcontext['city'] = kw['city_id']
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


class BrWebsiteMyAccount(CustomerPortal):

    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "cnpj_cpf",
                                "number", "district", "zipcode",
                                "company_type", "city_id", "state_id",
                                "country_id"]
    OPTIONAL_BILLING_FIELDS = ["street2"]

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        if "zip" in post:
            post["zipcode"] = post.pop("zip")
        return super(BrWebsiteMyAccount, self).account(
            redirect=redirect, **post)
