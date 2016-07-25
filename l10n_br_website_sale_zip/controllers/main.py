# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class L10nBrWebsiteSaleZip(main.website_sale):

    @http.route(['/shop/zip_search'], type='json', auth="public",
                methods=['POST'], website=True)
    def search_zip_json(self, zip):
        if len(zip) >= 8:
            cep = re.sub('[^0-9]', '', zip)
            zip_ids = request.env['l10n_br.zip'].sudo().zip_search_multi(
                zip_code=cep)

            if len(zip_ids) == 1:
                return {'sucesso': True,
                        'street': zip_ids[0].street,
                        'district': zip_ids[0].district,
                        'city_id': zip_ids[0].l10n_br_city_id.id,
                        'state_id': zip_ids[0].state_id.id,
                        'country_id': zip_ids[0].country_id.id}

        return {'sucesso': False}
