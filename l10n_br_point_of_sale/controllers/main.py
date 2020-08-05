# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import http
from odoo.http import request, Controller


class BrPosBaseController(Controller):

    @http.route(['/contact/get_cities'], type='json', auth="public",
                methods=['POST'], website=True)
    def get_cities_json(self, state_id):
        if state_id and isinstance(state_id, int):
            cities = request.env['res.state.city'].sudo().search(
                [('state_id', '=', state_id)])
            return [(city.id, city.name) for city in cities]
        return []

    @http.route(['/contact/get_states'], type='json', auth="public",
                methods=['POST'], website=True)
    def get_states_json(self, country_id):
        if country_id and isinstance(country_id, int):
            states = request.env['res.country.state'].sudo().search(
                [('country_id', '=', country_id)])
            return [(state.id, state.name) for state in states]
        return []

    @http.route(['/contact/zip_search'], type='json', auth="public",
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
