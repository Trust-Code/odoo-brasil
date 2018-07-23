# -*- coding: utf-8 -*-
# © 2018 Marina Domingues, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..tests.test_cnab_common import TestBrCnabPayment
import time


class TestBrCnabSicoob(TestBrCnabPayment):

    def get_voucher_id(self):
        account_voucher = self.env['account.voucher'].create({
            'partner_id': self.partner_fisica.id,
            'pay_now': 'pay_now',
            'account_date': time.strftime("%d/%m/%Y"),
            'journal_id': self.journalrec.id,
            'date': time.strftime("%d/%m/%Y"),
            'date_due': time.strftime("%d/%m/%Y"),
            'account_id': self.payable_account.id,
            'bank_account_id': self.receivable_account.id
        })
        return account_voucher.id

    def get_voucher_line(self):
        voucher_line = self.env['account.voucher.line'].create({
                'name': 'account_voucher',
                'quantity': 1.0,
                'price_unit': 150.0,
                'price_subtotal': 150.0,
                'account_id': self.payable_account.id,
                'voucher_id': self.get_voucher_id()
            })
        return voucher_line.voucher_id

    def get_payment_mode(self):
        sicoob = self.env['res.bank'].search([('bic', '=', '756')])
        conta = self.env['res.partner.bank'].create({
            'acc_number': '45425',  # 5 digitos
            'acc_number_dig': '0',  # 1 digito
            'bra_number': '4321',  # 4 digitos
            'bra_number_dig': '0',
            'codigo_convenio': '123458-8',  # 7 digitos
            'bank_id': sicoob.id,
        })
        mode = self.env['payment.mode'].create({
            'name': 'Sicoob TED',
            'type': 'payable',
            'payment_type': '01',
            'bank_account_id': conta.id
        })
        return mode.id

    def get_payment_order(self, payment_mode):
        self.payment_order = self.env['payment.order'].create({
            'name': 'cnab240_sicoob',
            'user_id': self.user.id,
            'payment_mode_id': payment_mode,
            'file_number': 1,
            'company_id': self.main_company.id,
            'type': 'payable',
            'data_emissao_cnab': time.strftime("%d/%m/%Y") + " " +
            time.strftime("%H:%M:%S")
        })
        return self.payment_order.id

    def set_order_lines(self, payment_order):
        nosso_numero = self.env['ir.sequence'].create({
                'name': "Nosso Numero"})
        info_id = self.get_payment_information()
        self.order_line = [
            (0, {
                    'type': 'payable',
                    'payment_order_id': payment_order.id,
                    'payment_mode_id': payment_order.payment_mode_id,
                    'value': 150.00,
                    'nosso_numero': nosso_numero,
                    'date_maturity': time.strftime("%d%m%Y"),
                    'state': 'open',
                    'value_final': 150.00,
                    'payment_information_id': info_id,
                    'voucher_id': self.get_voucher_line(),
                    'bank_account_id': self.receivable_account.id
                }),
            (0, {
                    'type': 'payable',
                    'payment_order_id': payment_order.id,
                    'payment_mode_id': payment_order.payment_mode_id,
                    'value': 120.00,
                    'nosso_numero': nosso_numero,
                    'date_maturity': time.strftime("%d%m%Y"),
                    'state': 'open',
                    'value_final': 120.00,
                    'payment_information_id': info_id,
                    'voucher_id': self.get_voucher_line(),
                    'bank_account_id': self.receivable_account.id
                    })
        ]

    def get_payment_information(self):
        payment_information = self.env[
            'l10n_br.payment_information'].create({
                'serv_type': '98',
                'mov_type': '0',
                'payment_type': '01',
                'mov_finality': '01',
                'warning_code': '0',
                'finality_ted': '11',
                'mov_instruc': '00',
                'rebate_value': 1.00,
                'discount_value': 2.00,
                'duty_value': 3.00,
                'mora_value': 1.00,
                'credit_hist_code': '2644',
                'operation_code': '018'
            })
        return payment_information.id

    def get_cnab(self):
        ordem_cobranca = self.env[
            'payment.order'].browse(self.get_payment_order(pay_mode))
        self.set_order_lines(ordem_cobranca)
        ordem_cobranca.action_generate_payable_cnab()
        return ordem_cobranca.cnab_file

    def test_create_cnab(self):
        pay_mode = self.get_payment_mode()
        ordem_cobranca = self.env[
            'payment.order'].browse(self.get_payment_order(pay_mode))
        self.set_order_lines(ordem_cobranca)
        ordem_cobranca.action_generate_payable_cnab()
        self.cnab = ordem_cobranca.cnab_file

    def test_size_arq(self):
        cnab = self.get_cnab()
        self.assertEquals(len(cnab), 7)
        for line in self.cnab:
            self.assertEquals(len(line), 240)

    def test_header_arq(self):
        arq_teste = self.get_cnab()._get_header_arq()
        arq_ok = {
            'cedente_inscricao_tipo': 2,
            'cedente_inscricao_numero': '92743275000133',
            'codigo_convenio': 1234588,
            'cedente_agencia': '4321',
            'cedente_agencia_dv': '0',
            'cedente_conta': 45425,
            'cedente_conta_dv': 0,
            'cedente_nome': 'Trustcode',
            'data_geracao_arquivo': time.strftime("%d%m%Y"),
            'hora_geracao_arquivo': time.strftime("%H%M%S"),
            'numero_sequencial_arquivo': 1,
        }
        self.assertEquals(arq_ok, arq_teste)
