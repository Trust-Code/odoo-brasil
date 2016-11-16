# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'purchase.order'

    partner_contact_id = fields.Many2one('res.partner',
                                         string='Contato de Venda')
    partner_is_company = fields.Boolean()

    @api.onchange('partner_id')
    def _br_sale_contact_onchange_partner_id(self):
        self.partner_contact_id = None
        self.partner_is_company = False
        if self.partner_id.is_company:
            self.partner_is_company = True
        if self.partner_is_company and len(self.partner_id.child_ids) == 1:
            self.partner_contact_id = self.partner_id.child_ids[0]
