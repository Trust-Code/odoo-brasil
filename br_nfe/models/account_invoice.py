# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_edoc_vals(self, inv):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv)
        res['ambiente'] = 'homologacao' \
            if inv.company_id.tipo_ambiente == '2' else 'producao'
        if inv.partner_id.is_company:
            res['ind_final'] = '0'
        else:
            res['ind_final'] = '1'
        if inv.fiscal_position_id.ind_final:
            res['ind_final'] = inv.fiscal_position_id.ind_final
        res['ind_pres'] = inv.fiscal_position_id.ind_pres
        return res
