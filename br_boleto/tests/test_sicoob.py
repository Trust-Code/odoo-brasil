# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.addons.br_boleto.tests.test_common import TestBoleto


class TestBoletoSicoob(TestBoleto):

    def _return_payment_mode(self):
        super(TestBoletoSicoob, self)._return_payment_mode()
        sequencia = self.env['ir.sequence'].create({
            'name': u"Nosso Número"
        })
        sicoob = self.env['res.bank'].search([('bic', '=', '756')])
        conta = self.env['res.partner.bank'].create({
            'acc_number': '12345',  # 5 digitos
            'acc_number_dig': '0',  # 1 digito
            'bra_number': '1234',  # 4 digitos
            'bra_number_dig': '0',
            'codigo_convenio': '123456-7',  # 7 digitos
            'bank_id': sicoob.id,
        })
        journal = self.env['account.journal'].create({
            'name': 'Banco Sicoob',
            'code': 'SIC',
            'type': 'bank',
            'bank_account_id': conta.id,
            'company_id': self.main_company.id,
        })
        mode = self.env['l10n_br.payment.mode'].create({
            'name': 'Sicoob',
            'boleto': True,
            'boleto_type': '9',
            'boleto_carteira': '1',
            'boleto_modalidade': '01',
            'nosso_numero_sequence': sequencia.id,
            'journal_id': journal.id,
        })
        return mode.id

    def setUp(self):
        super(TestBoletoSicoob, self).setUp()

    # Não precisa fazer essa validação em outras classes
    def test_basic_validation(self):
        with self.assertRaises(UserError):
            self.invoices.action_invoice_open()

    def _update_main_company(self):
        self.main_company.write({
            'name': 'Trustcode',
            'legal_name': 'Trustcode Tecnologia da Informação',
            'cnpj_cpf': '92.743.275/0001-33',
            'inscr_est': '219.882.606',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
        })

    def _update_partner_fisica(self):
        self.partner_fisica.write({
            'cnpj_cpf': '075.932.961-30',
            'district': 'Centro',
            'zip': '88032-050',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
        })

    def test_raise_error_if_not_payment(self):
        self._update_main_company()
        self._update_partner_fisica()
        self.invoices.action_invoice_open()

        self.assertEquals(len(self.invoices.receivable_move_line_ids), 1)

        move = self.invoices.receivable_move_line_ids[0]
        vals = move.action_print_boleto()

        self.assertEquals(vals['report_name'], 'br_boleto.report.print')
        self.assertEquals(vals['report_type'], 'qweb-pdf')

        vals = self.invoices.action_print_boleto()

        self.assertEquals(vals['report_name'], 'br_boleto.report.print')
        self.assertEquals(vals['report_type'], 'qweb-pdf')

        line_ids = self.env['payment.order.line'].action_register_boleto(
            self.invoices.receivable_move_line_ids)

        boleto_list = line_ids.generate_boleto_list()
        boleto = boleto_list[0]
        self.assertEquals(len(boleto_list), 1)
        self.assertEquals(boleto.valor_documento, '1000.00')
        self.assertEquals(boleto.valor, '1000.00')

        self.assertEquals(boleto.cedente_documento, self.main_company.cnpj_cpf)
        self.assertEquals(
            boleto.sacado_documento, self.partner_fisica.cnpj_cpf)
