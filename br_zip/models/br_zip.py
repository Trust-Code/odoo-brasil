# -*- coding: utf-8 -*-
# © 2012  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import logging
import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class BrZip(models.Model):
    _name = 'br.zip'
    _description = u'CEP'
    _rec_name = 'zip'

    zip = fields.Char('CEP', size=8, required=True)
    street_type = fields.Char('Tipo', size=26)
    street = fields.Char('Logradouro', size=72)
    district = fields.Char('Bairro', size=72)
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one(
        'res.country.state', 'Estado',
        domain="[('country_id','=',country_id)]")
    city_id = fields.Many2one(
        'res.state.city', 'Cidade',
        required=True, domain="[('state_id','=',state_id)]")

    def set_domain(self, country_id=False, state_id=False,
                   city_id=False, district=False,
                   street=False, zip_code=False):
        domain = []
        if zip_code:
            new_zip = re.sub('[^0-9]', '', zip_code or '')
            domain.append(('zip', '=', new_zip))
        else:
            if not state_id or not city_id or \
                    len(street or '') == 0:
                raise UserError(
                    u'Necessário informar Estado, município e logradouro')

            if country_id:
                domain.append(('country_id', '=', country_id))
            if state_id:
                domain.append(('state_id', '=', state_id))
            if city_id:
                domain.append(('city_id', '=', city_id))
            if district:
                domain.append(('district', 'ilike', district))
            if street:
                domain.append(('street', 'ilike', street))

        return domain

    def set_result(self, zip_obj=None):
        if zip_obj:
            zip_code = zip_obj.zip
            if len(zip_code) == 8:
                zip_code = '%s-%s' % (zip_code[0:5], zip_code[5:8])
            result = {
                'country_id': zip_obj.country_id.id,
                'state_id': zip_obj.state_id.id,
                'city_id': zip_obj.city_id.id,
                'district': zip_obj.district,
                'street': ((zip_obj.street_type or '') +
                           ' ' + (zip_obj.street or '')) if
                zip_obj.street_type else (zip_obj.street or ''),
                'zip': zip_code,
            }
        else:
            result = {}
        return result

    def zip_search_multi(self, country_id=False,
                         state_id=False, city_id=False,
                         district=False, street=False, zip_code=False):
        domain = self.set_domain(
            country_id=country_id,
            state_id=state_id,
            city_id=city_id,
            district=district,
            street=street,
            zip_code=zip_code)
        zip_ids = self.search(domain)
        if len(zip_ids) == 0:
            zip_code = re.sub('[^0-9]', '', zip_code or '')
            if zip_code and len(zip_code) == 8:
                self._search_by_cep(zip_code)
            elif zip_code:
                raise UserError(u'Digite o cep corretamente')
            else:
                self._search_by_address(state_id, city_id, street)

            return self.search(domain)
        else:
            return zip_ids

    def _search_by_cep(self, zip_code):
        try:
            url_viacep = 'http://viacep.com.br/ws/' + \
                zip_code + '/json/unicode/'
            obj_viacep = requests.get(url_viacep)
            res = obj_viacep.json()
            if not res.get('erro', False):
                city = self.env['res.state.city'].search(
                    [('ibge_code', '=', res['ibge'][2:]),
                     ('state_id.code', '=', res['uf'])])

                self.env['br.zip'].create(
                    {'zip': re.sub('[^0-9]', '', res['cep']),
                     'street': res['logradouro'],
                     'district': res['bairro'],
                     'country_id': city.state_id.country_id.id,
                     'state_id': city.state_id.id,
                     'city_id': city.id})

        except Exception as e:
            _logger.error(e.message, exc_info=True)

    def _search_by_address(self, state_id, city_id, street):
        try:
            city = self.env['res.state.city'].browse(city_id)
            url_viacep = 'http://viacep.com.br/ws/' + city.state_id.code + \
                '/' + city.name + '/' + street + '/json/unicode/'
            obj_viacep = requests.get(url_viacep)
            results = obj_viacep.json()
            if results:
                for res in results:
                    city = self.env['res.state.city'].search(
                        [('ibge_code', '=', res['ibge'][2:]),
                         ('state_id.code', '=', res['uf'])])

                    self.env['br.zip'].create(
                        {'zip': re.sub('[^0-9]', '', res['cep']),
                         'street': res['logradouro'],
                         'district': res['bairro'],
                         'country_id': city.state_id.country_id.id,
                         'state_id': city.state_id.id,
                         'city_id': city.id})

        except Exception as e:
            _logger.error(e.message, exc_info=True)

    @api.multi
    def search_by_zip(self, zip_code):
        zip_ids = self.zip_search_multi(zip_code=zip_code)
        if len(zip_ids) == 1:
            return self.set_result(zip_ids[0])
        else:
            raise UserError(_(u'Nenhum CEP encontrado'))

    @api.multi
    def seach_by_address(self, obj, country_id=False, state_id=False,
                         city_id=False, district=False, street=False):

        zip_ids = self.zip_search_multi(
            country_id=country_id, state_id=state_id,
            city_id=city_id, district=district, street=street)

        if len(zip_ids) == 1:
            res = self.set_result(zip_ids[0])
            return res
        else:
            if len(zip_ids) > 1:
                obj_zip_result = self.env['br.zip.result']
                zip_ids = obj_zip_result.map_to_zip_result(
                    zip_ids, obj._name, obj.id)

                return self.create_wizard(
                    obj._name,
                    obj.id,
                    country_id=obj.country_id.id,
                    state_id=obj.state_id.id,
                    city_id=obj.city_id.id,
                    district=obj.district,
                    street=obj.street,
                    zip_code=obj.zip,
                    zip_ids=[z.id for z in zip_ids]
                )
            else:
                raise UserError(_(u'Nenhum registro encontrado'))

    def create_wizard(self, object_name, address_id, country_id=False,
                      state_id=False, city_id=False,
                      district=False, street=False, zip_code=False,
                      zip_ids=False):
        context = dict(self.env.context)
        context.update({
            'zip': zip_code,
            'street': street,
            'district': district,
            'country_id': country_id,
            'state_id': state_id,
            'city_id': city_id,
            'zip_ids': zip_ids,
            'address_id': address_id,
            'object_name': object_name})

        result = {
            'name': u'Zip Search',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'br.zip.search',
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        }

        return result
