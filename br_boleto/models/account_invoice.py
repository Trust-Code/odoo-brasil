# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_mode_id = fields.Many2one('payment.mode',
                                      string=u"Modo de pagamento")

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        res = super(AccountInvoice, self).\
            finalize_invoice_move_lines(move_lines)

        for invoice_line in res:
            line = invoice_line[2]
            line['payment_mode_id'] = self.payment_mode_id.id
        return res

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        error = ''
        for item in self:
            if item.payment_mode_id and item.payment_mode_id.name == u'Boleto':
                if not self.company_id.partner_id.legal_name:
                    error += u'Razão Social\n'
                if not self.company_id.cnpj_cpf:
                    error += u'CNPJ\n'
                if not self.company_id.district:
                    error += u'Bairro\n'
                if not self.company_id.zip:
                    error += u'CEP\n'
                if not self.company_id.city_id.name:
                    error += u'Cidade\n'
                if not self.company_id.street:
                    error += u'Logradouro\n'
                if not self.company_id.number:
                    error += u'Número\n'
                if not self.company_id.state_id.code:
                    error += u'Estado\n'
                if len(error) > 0:
                    raise UserError(u"""Ação Bloqueada!
Para prosseguir é necessário preencher os seguintes campos nas configurações \
da empresa:\n""" + error)
        return res

    @api.multi
    def action_register_boleto(self):
        if self.state in ('draft', 'cancel'):
            raise UserError(
                'Fatura provisória ou cancelada não permite emitir boleto')
        self = self.with_context({'origin_model': 'account.invoice'})
        return self.env['report'].get_action(self.id, 'br_boleto.report.print')
