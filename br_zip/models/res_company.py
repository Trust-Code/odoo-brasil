# -*- coding: utf-8 -*-
# © 2004-2010 Tiny SPRL (<http://tiny.be>)
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def zip_search(self):
        self.ensure_one()
        res = self.env['br.zip'].zip_search(country_id=self.country_id.id,
                                            state_id=self.state_id.id,
                                            city_id=self.city_id.id,
                                            district=self.district,
                                            street=self.street,
                                            zip_code=self.zip)
        self.update(res)
