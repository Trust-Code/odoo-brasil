# -*- coding: utf-8 -*-
# © 2004-2010 Tiny SPRL (<http://tiny.be>)
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def zip_search(self):
        return self.partner_id.zip_search()
