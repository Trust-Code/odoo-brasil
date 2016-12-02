# -*- coding: utf-8 -*-
# © 2010-2012  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('zip')
    def _onchange_field(self):
        if self.type != 'contact':
            self.zip_search()

    @api.multi
    def zip_search(self):
        self.ensure_one()
        res = self.env['br.zip'].zip_search(obj_name=self,
                                            country_id=self.country_id.id,
                                            state_id=self.state_id.id,
                                            city_id=self.city_id.id,
                                            district=self.district,
                                            street=self.street,
                                            zip_code=self.zip)
        return res
