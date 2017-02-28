# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        error = ''
        for item in self:
            if item.payment_mode_id and item.payment_mode_id.boleto_type != '':
                if not self.company_id.partner_id.legal_name:
                    error += u'Empresa - Razão Social\n'
                if not self.company_id.cnpj_cpf:
                    error += u'Empresa - CNPJ\n'
                if not self.company_id.district:
                    error += u'Empresa - Bairro\n'
                if not self.company_id.zip:
                    error += u'Empresa - CEP\n'
                if not self.company_id.city_id.name:
                    error += u'Empresa - Cidade\n'
                if not self.company_id.street:
                    error += u'Empresa - Logradouro\n'
                if not self.company_id.number:
                    error += u'Empresa - Número\n'
                if not self.company_id.state_id.code:
                    error += u'Empresa - Estado\n'

                if not self.commercial_partner_id.name:
                    error += u'Cliente - Nome\n'
                if self.commercial_partner_id.is_company and \
                   not self.commercial_partner_id.legal_name:
                    error += u'Cliente - Razão Social\n'
                if not self.commercial_partner_id.cnpj_cpf:
                    error += u'Cliente - CNPJ/CPF \n'
                if not self.commercial_partner_id.district:
                    error += u'Cliente - Bairro\n'
                if not self.commercial_partner_id.zip:
                    error += u'Cliente - CEP\n'
                if not self.commercial_partner_id.city_id.name:
                    error += u'Cliente - Cidade\n'
                if not self.commercial_partner_id.street:
                    error += u'Cliente - Logradouro\n'
                if not self.commercial_partner_id.number:
                    error += u'Cliente - Número\n'
                if not self.commercial_partner_id.state_id.code:
                    error += u'Cliente - Estado\n'

                if len(error) > 0:
                    raise UserError(u"""Ação Bloqueada!
Para prosseguir é necessário preencher os seguintes campos:\n""" + error)
        return res

    @api.multi
    def action_register_boleto(self):
        if self.state in ('draft', 'cancel'):
            raise UserError(
                u'Fatura provisória ou cancelada não permite emitir boleto')
        self = self.with_context({'origin_model': 'account.invoice'})
        return self.env['report'].get_action(self.id, 'br_boleto.report.print')
