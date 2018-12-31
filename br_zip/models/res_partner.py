# -*- coding: utf-8 -*-
# © 2010-2012  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('zip')
    def _onchange_zip(self):
        cep = re.sub('[^0-9]', '', self.zip or '')
        if len(cep) == 8:
            self.zip_search(cep)

    @api.multi
    def zip_search(self, cep):
        self.zip = "%s-%s" % (cep[0:5], cep[5:8])
        res = self.env['br.zip'].search_by_zip(zip_code=self.zip)
        if res:
            self.update(res)

    @api.onchange('street', 'city_id', 'district')
    def _search_street(self):
        if self.street and self.city_id:
            res = self.env['br.zip'].search_by_address(
                country_id=self.city_id.state_id.country_id.id,
                state_id=self.city_id.state_id.id,
                city_id=self.city_id.id,
                street=self.street,
                obj=None,
                district=self.district,
                error=False
            )
            if res:
                self.update(res)
