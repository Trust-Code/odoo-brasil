# © 2018 Marina Domingues, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
import base64
from decimal import Decimal

from odoo.addons.br_payment_cnab.tests.test_common import TestBrCnabPayment
from odoo.addons.br_payment_cnab.bancos.sicoob import Sicoob240

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class TestBrCnabSicoob(TestBrCnabPayment):

    def setUp(self):
        super(TestBrCnabSicoob, self).setUp()
        payment_mode = self.get_payment_mode()
        self.payment_order = self.set_payment_order(payment_mode)
        self.set_order_lines()

    def get_voucher_id(self):
        account_voucher = self.env['account.voucher'].create({
            'partner_id': self.partner_fisica.id,
            'pay_now': 'pay_now',
            'account_date': time.strftime(DATE_FORMAT),
            'journal_id': self.journalrec.id,
            'date': time.strftime(DATE_FORMAT),
            'date_due': time.strftime(DATE_FORMAT),
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
            'account_id': self.expense_account.id,
            'voucher_id': self.get_voucher_id()
        })
        return voucher_line.voucher_id

    def get_payment_mode(self):
        nosso_numero = self.env['ir.sequence'].create({
            'name': "Nosso Numero"})
        sicoob = self.env['res.bank'].search([('bic', '=', '756')])
        conta = self.env['res.partner.bank'].create({
            'acc_number': '45425',  # 5 digitos
            'acc_number_dig': '0',  # 1 digito
            'bra_number': '4321',  # 4 digitos
            'bra_number_dig': '0',
            'l10n_br_convenio_pagamento': '123458-8',  # 7 digitos
            'bank_id': sicoob.id,
            'partner_id': self.main_company.partner_id.id,
        })
        journal = self.env['account.journal'].create({
            'name': 'Banco Sicoob',
            'code': 'SIC',
            'type': 'bank',
            'bank_account_id': conta.id,
            'company_id': self.main_company.id,
            'l10n_br_sequence_nosso_numero': nosso_numero.id,
        })
        payment_mode = self.env['l10n_br.payment.mode'].create({
            'name': 'Sicoob TED',
            'type': 'payable',
            'payment_type': '01',
            'journal_id': journal.id,
        })
        return payment_mode

    def set_payment_order(self, payment_mode):
        self.payment_order = self.env['payment.order'].create({
            'name': 'cnab240_sicoob',
            'user_id': self.user.id,
            'payment_mode_id': payment_mode.id,
            'file_number': 1,
            'company_id': self.main_company.id,
            'type': 'payable',
            'data_emissao_cnab': time.strftime(DTFT),
            'src_bank_account_id': payment_mode.journal_id.bank_account_id.id,
        })
        return self.payment_order

    def set_order_lines(self):
        order_lines = []
        nosso_numero = self.env['ir.sequence'].create({
            'name': "Nosso Numero"})
        info_id = self.get_payment_information()
        order_lines.append(self.env['payment.order.line'].create({
            'type': 'payable',
            'partner_id': self.partner_fisica.id,
            'payment_order_id': self.payment_order.id,
            'payment_mode_id': self.payment_order.payment_mode_id.id,
            'src_bank_account_id':
            self.payment_order.payment_mode_id.journal_id.bank_account_id.id,
            'amount_total': 150.00,
            'nosso_numero': nosso_numero.next_by_id(),
            'date_maturity': time.strftime(DATE_FORMAT),
            'state': 'sent',
            'value_final': 150.00,
            'payment_information_id': info_id.id,
            'rebate_value': 1.00,
            'discount_value': 2.00,
            'fine_value': 3.00,
            'interest_value': 1.00,
            'voucher_id': self.get_voucher_line().id,
            'bank_account_id': self.receivable_account.id,
        }))
        order_lines.append(self.env['payment.order.line'].create({
            'type': 'payable',
            'partner_id': self.partner_fisica.id,
            'payment_order_id': self.payment_order.id,
            'payment_mode_id': self.payment_order.payment_mode_id.id,
            'src_bank_account_id':
            self.payment_order.payment_mode_id.journal_id.bank_account_id.id,
            'amount_total': 120.00,
            'nosso_numero': nosso_numero.next_by_id(),
            'date_maturity': time.strftime(DATE_FORMAT),
            'state': 'sent',
            'value_final': 120.00,
            'payment_information_id': info_id.id,
            'rebate_value': 1.00,
            'discount_value': 2.00,
            'fine_value': 3.00,
            'interest_value': 1.00,
            'voucher_id': self.get_voucher_line().id,
            'bank_account_id': self.receivable_account.id,
        }))
        return [line.id for line in order_lines]

    def get_payment_information(self):
        payment_information = self.env[
            'l10n_br.payment_information'].create({
                'service_type': '98',
                'mov_type': '0',
                'payment_type': '01',
                'mov_finality': '01',
                'warning_code': '0',
                'mov_instruc': '00',
                'credit_hist_code': '2644',
                'operation_code': '018',
                'percentual_receita_bruta_acumulada': Decimal('12.00')
            })
        return payment_information

    def get_cnab_obj(self, ordem_cobranca):
        cnab = Sicoob240(ordem_cobranca)
        cnab.create_cnab(ordem_cobranca.line_ids)
        return cnab

    def get_cnab_file(self):
        self.payment_order.action_generate_payable_cnab()
        cnab = base64.decodestring(self.payment_order.cnab_file)
        cnab = cnab.decode('utf-8').split('\r\n')
        cnab.pop()
        return cnab

    def test_size_arq(self):
        cnab = self.get_cnab_file()
        self.assertEquals(len(cnab), 8)
        for line in cnab:
            self.assertEquals(len(line), 240)

    def test_header_arq(self):
        cnab = self.get_cnab_obj(self.payment_order)
        arq_teste = cnab._get_header_arq()
        arq_ok = {
            'cedente_inscricao_tipo': 2,
            'cedente_inscricao_numero': 92743275000133,
            'codigo_convenio': 1234588,
            'cedente_agencia': 4321,
            'cedente_agencia_dv': '0',
            'cedente_conta': 45425,
            'cedente_conta_dv': 0,
            'cedente_nome': 'Trustcode Tecnologia da Inform',
            'data_geracao_arquivo': int(time.strftime("%d%m%Y")),
            'hora_geracao_arquivo': int(time.strftime("%H%M%S")[:4]),
            'numero_sequencial_arquivo': 1,
        }
        self.assertEquals(arq_ok, arq_teste)

    def test_header_lot(self):
        cnab = self.get_cnab_obj(self.payment_order)
        lot_teste = cnab._get_header_lot(
            self.payment_order.line_ids[1], 1, '41')
        lot_ok = {
            'controle_lote': 1,
            'cedente_agencia': 4321,
            'cedente_uf': 'SC',
            'tipo_servico': 98,
            'cedente_endereco_numero': 42,
            'codigo_convenio': 1234588,
            'forma_lancamento': '41',
            'cedente_endereco_complemento': '',
            'cedente_cep_complemento': 240,
            'cedente_conta_dv': 0,
            'cedente_agencia_dv': '0',
            'mensagem1': '',
            'cedente_nome': 'Trustcode Tecnologia da Inform',
            'cedente_cep': 88037,
            'cedente_cidade': 'Florianópolis',
            'cedente_conta': 45425,
            'cedente_inscricao_tipo': 2,
            'cedente_endereco_rua': 'Vinicius de Moraes',
            'cedente_inscricao_numero': 92743275000133
        }
        for key, value in lot_ok.items():
            self.assertEquals(value, lot_teste[key], 'Key: %s' % key)

    def test_seg(self):
        cnab = self.get_cnab_obj(self.payment_order)
        seg_teste = cnab._get_segmento(
            self.payment_order.line_ids[0], 1, 1, 'SegmentoA')
        seg_ok = {
            'controle_lote': 1,
            'sequencial_registro_lote': 1,
            'tipo_movimento': 0,
            'codigo_instrucao_movimento': 0,
            'codigo_camara_compensacao': 18,
            'favorecido_codigo_banco':
                'BANCO COOPERATIVO DO BRASIL S.A. (SICOOB)',
            'favorecido_banco': 756,
            'favorecido_agencia': 1234,
            'favorecido_agencia_dv': '0',
            'favorecido_conta': 12345,
            'favorecido_conta_dv': 0,
            'favorecido_agencia_conta_dv': '',
            'favorecido_nome': 'Razão Social',
            'favorecido_doc_numero': 54577015498,
            'numero_documento_cliente': '2',
            'data_pagamento': int(time.strftime("%d%m%Y")),
            'valor_pagamento': Decimal('120.00'),
            'data_real_pagamento': int(time.strftime("%d%m%Y")),
            'valor_real_pagamento': Decimal('121.00'),
            'mensagem2': '',
            'finalidade_doc_ted': '01',
            'favorecido_emissao_aviso': 0,
            'favorecido_inscricao_tipo': 1,
            'favorecido_inscricao_numero': 54577015498,
            'favorecido_endereco_rua': 'Endereço Rua',
            'favorecido_endereco_numero': 42,
            'favorecido_endereco_complemento': '',
            'favorecido_bairro': 'Centro',
            'favorecido_cidade': 'Florianópolis',
            'favorecido_cep': 88037240,
            'favorecido_uf': 'SC',
            'valor_documento': Decimal('120.00'),
            'valor_abatimento': Decimal('1.00'),
            'valor_desconto': Decimal('2.00'),
            'valor_mora': Decimal('1.00'),
            'valor_multa': Decimal('3.00'),
            'hora_envio_ted': (int(time.strftime("%H%M%S")[0:4])),
            'codigo_historico_credito': '2644',
            'cedente_nome': 'Trustcode Tecnologia da Inform',
            'valor_nominal_titulo': Decimal('120.00'),
            'valor_desconto_abatimento': Decimal('3.00'),
            'valor_multa_juros': Decimal('4.00'),
            'codigo_moeda': 9,
            'codigo_de_barras': 0,
            'codigo_de_barras_alfa': '',
            'nome_concessionaria': 'Razão Social',
            'data_vencimento': int(time.strftime("%d%m%Y")),
            'contribuinte_nome': 'Trustcode Tecnologia da Inform',
            'codigo_receita_tributo': '',
            'tipo_identificacao_contribuinte': 1,
            'identificacao_contribuinte': 92743275000133,
            'codigo_identificacao_tributo': '',
            'mes_ano_competencia': 0,
            'valor_previsto_inss': Decimal('120.00'),
            'periodo_apuracao': 0,
            'valor_principal': Decimal('120.00'),
            'valor_juros_encargos': Decimal('1.00'),
            'valor_receita_bruta_acumulada': Decimal('0.0'),
            'inscricao_estadual': 219882606,
            'valor_receita': Decimal('120.0'),
            'numero_referencia': 0,
            'percentual_receita_bruta_acumulada': Decimal('12.00')}
        for key, value in seg_ok.items():
            self.assertEquals(value, seg_teste[key], 'Key: %s' % key)
