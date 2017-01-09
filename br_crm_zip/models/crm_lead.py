# -*- coding: utf-8 -*-
# © 2011  Fabio Negrini - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import models, api


class CrmLead(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"

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
