# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    indPag = fields.Selection(
        [('0', u'Pagamento à Vista'), ('1', u'Pagamento à Prazo'),
         ('2', 'Outros')], 'Indicador de Pagamento', default='1')


class AccountAccount(models.Model):
    _inherit = 'account.account'

    code_first_digit = fields.Char(compute='_compute_code_first_digit',
                                   string=u'Primeiro Dígito',
                                   store=True)

    @api.multi
    @api.depends('code')
    def _compute_code_first_digit(self):
        for rec in self:
            rec.code_first_digit = rec.code[0] if rec.code else ''
