# -*- coding: utf-8 -*-
#    Copyright (C) 2016 MultidadosTI (http://www.multidadosti.com.br)
#    @author Michell Stuttgart <m.faria@itimpacta.org.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class ResBank(models.Model):
    _inherit = 'res.bank'

    @api.onchange('zip')
    def _onchange_field(self):
        if self.zip and len(self.zip.replace('-', '')) == 8:
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
