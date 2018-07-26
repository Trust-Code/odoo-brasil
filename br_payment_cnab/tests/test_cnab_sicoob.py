# -*- coding: utf-8 -*-
# © 2018 Marina Domingues, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..tests.test_cnab_common import TestBrCnabPayment
from ..bancos.sicoob import Sicoob240
import time
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class TestBrCnabSicoob(TestBrCnabPayment):

    def setUp(self):
        super(TestBrCnabSicoob, self).setUp()
        pay_mode = self.get_payment_mode()
        self.payment_order = self.set_payment_order(pay_mode)
        self.set_order_lines()

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

    def set_payment_order(self, payment_mode):
        self.payment_order = self.env['payment.order'].create({
            'name': 'cnab240_sicoob',
            'user_id': self.user.id,
            'payment_mode_id': payment_mode,
            'file_number': 1,
            'company_id': self.main_company.id,
            'type': 'payable',
            'data_emissao_cnab': time.strftime(DTFT)
        })
        return self.payment_order.id

    def set_order_lines(self):
        order_lines = []
        nosso_numero = self.env['ir.sequence'].create({
            'name': "Nosso Numero"})
        ordem_cobranca = self.env['payment.order'].browse(self.payment_order)
        info_id = self.get_payment_information()
        order_lines.append(self.env['payment.order.line'].create({
            'type': 'payable',
            'partner_id': self.partner_fisica.id,
            'payment_order_id': ordem_cobranca.id,
            'payment_mode_id': ordem_cobranca.payment_mode_id.id,
            'value': 150.00,
            'nosso_numero': nosso_numero.next_by_id(),
            'date_maturity': time.strftime(DATE_FORMAT),
            'state': 'open',
            'value_final': 150.00,
            'payment_information_id': info_id,
            'voucher_id': self.get_voucher_line().id,
            'bank_account_id': self.receivable_account.id,
        }))
        order_lines.append(self.env['payment.order.line'].create({
            'type': 'payable',
            'partner_id': self.partner_fisica.id,
            'payment_order_id': ordem_cobranca.id,
            'payment_mode_id': ordem_cobranca.payment_mode_id.id,
            'value': 120.00,
            'nosso_numero': nosso_numero.next_by_id(),
            'date_maturity': time.strftime(DATE_FORMAT),
            'state': 'open',
            'value_final': 120.00,
            'payment_information_id': info_id,
            'voucher_id': self.get_voucher_line().id,
            'bank_account_id': self.receivable_account.id,
        }))
        return [line.id for line in order_lines]

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

    def get_cnab_obj(self, ordem_cobranca):
        cnab = Sicoob240(ordem_cobranca)
        cnab.create_cnab(ordem_cobranca.line_ids)
        return cnab

    def get_cnab_file(self):
        ordem_cobranca = self.env['payment.order'].browse(self.payment_order)
        ordem_cobranca.action_generate_payable_cnab()
        cnab = base64.decodestring(ordem_cobranca.cnab_file)
        cnab = cnab.decode('utf-8').split('\r\n')
        cnab.pop()
        return cnab

    def test_size_arq(self):
        cnab = self.get_cnab_file()
        self.assertEquals(len(cnab), 8)
        for line in cnab:
            self.assertEquals(len(line), 240)

    def test_header_arq(self):
        ordem_cobranca = self.env['payment.order'].browse(self.payment_order)
        cnab = self.get_cnab_obj(ordem_cobranca)
        arq_teste = cnab._get_header_arq()
        arq_ok = {
            'cedente_inscricao_tipo': 2,
            'cedente_inscricao_numero': 92743275000133,
            'codigo_convenio': '1234588',
            'cedente_agencia': 4321,
            'cedente_agencia_dv': '0',
            'cedente_conta': 45425,
            'cedente_conta_dv': 0,
            'cedente_nome': 'Trustcode',
            'data_geracao_arquivo': int(time.strftime("%d%m%Y")),
            'hora_geracao_arquivo': int(time.strftime("%H%M%S")[:4]),
            'numero_sequencial_arquivo': 1,
        }
        self.assertEquals(arq_ok, arq_teste)

    def test_header_lot(self):
        ordem_cobranca = self.env['payment.order'].browse(self.payment_order)
        cnab = self.get_cnab_obj(ordem_cobranca)
        lot_teste = cnab._get_header_lot(ordem_cobranca.line_ids[1], 1)
        lot_ok = {
            'controle_lote': 1,
            'cedente_agencia': 4321,
            'cedente_uf': 'SC',
            'tipo_servico': 98,
            'cedente_endereco_numero': 42,
            'codigo_convenio': '123458-8',
            'forma_lancamento': '41',
            'cedente_endereco_complemento': '',
            'cedente_cep_complemento': 240,
            'cedente_conta_dv': 0,
            'cedente_agencia_dv': '0',
            'mensagem1': '                                        ',
            'cedente_nome': 'Trustcode',
            'cedente_cep': 88037,
            'cedente_cidade': 'Florianópolis',
            'cedente_conta': 45425,
            'cedente_inscricao_tipo': 2,
            'cedente_endereco_rua': 'Vinicius de Moraes',
            'cedente_inscricao_numero': 92743275000133
        }
        self.assertEquals(lot_ok, lot_teste)

    def test_seg_A(self):
        ordem_cobranca = self.env['payment.order'].browse(self.payment_order)
        cnab = self.get_cnab_obj(ordem_cobranca)
        seg_teste = cnab._get_header_lot(ordem_cobranca.line_ids[1], 1)
        seg_ok = {
            'cedente_agencia': 4321,
            'cedente_agencia_dv': '0',
            'cedente_cep': 88037,
            'cedente_cep_complemento': 240,
            'cedente_cidade': 'Florianópolis',
            'cedente_conta': 45425,
            'cedente_conta_dv': 0,
            'cedente_endereco_complemento': '',
            'cedente_endereco_numero': 42,
            'cedente_endereco_rua': 'Vinicius de Moraes',
            'cedente_inscricao_numero': 92743275000133,
            'cedente_inscricao_tipo': 2,
            'cedente_nome': 'Trustcode',
            'cedente_uf': 'SC',
            'codigo_convenio': '123458-8',
            'controle_lote': 1,
            'forma_lancamento': '41',
            'mensagem1': '                                        ',
            'tipo_servico': 98
        }

        self.assertEquals(seg_ok, seg_teste)

    def sequency_lot(self):
        cnab = self.get_cnab_file()
        self.assertEquals(len(cnab), 8)
        for i in range(2, len(cnab)):
            self.assertEquals(cnab[i][13], i-1)
