# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from random import randint
import re
from .test_cnab_common import TestCnab
#  from odoo.exceptions import UserError, AccessError


class TestCnabSicoob(TestCnab):

    def setUp(self):
        super(TestCnabSicoob, self).setUp()
        self.banco_sicoob = self.env['res.bank'].search([('bic', '=', '756')],
                                                        limit=1)
        self.conta_sicoob = self.env['res.partner.bank'].create({
            'acc_number': ''.join([str(randint(0, 9)) for i in range(5)]),
            'acc_number_dig': str(randint(0, 9)),
            'bra_number': ''.join([str(randint(0, 9)) for i in range(4)]),
            'bra_number_dig': str(randint(0, 9)),
            'codigo_convenio': '%s-%d' % (
                ''.join([str(randint(0, 9)) for i in range(6)]),
                randint(0, 9)),
            'bank_id': self.banco_sicoob.id
        })

        self.tipo_pagamento = self.env['payment.type'].create({
            'name': 'CNAB240 - Sicoob', 'code': '240-9'
        })

        self.modo_pagamento = self.env['payment.mode'].create({
            'name': 'Boleto Sicoob',
            'bank_account_id': self.conta_sicoob.id,
            'boleto_type': '9', 'payment_type_id': self.tipo_pagamento.id,
            'boleto_carteira': '1', 'boleto_modalidade': '01',
            'instrucoes': "Lorem ipsum dolor sit amet, consectetur adipiscing",
             })

        self.account_move_line = self.env['account.move.line'].create({
            'name': str(self.env['ir.sequence'].
                        next_by_code('doc.number.cnab')),
            'partner_id': self.parceiro.id,
            'journal_id': self.account_journal_model.id,
            'account_id': self.account_receivable.id,
            'debit': self.produto_produto.list_price,
            'payment_mode_id': self.modo_pagamento.id,
            'nosso_numero': self.env['ir.sequence'].
            next_by_code('nosso_numero.sicoob')
        })

        self.ordem_cobranca = self.env['payment.order'].create({
            'name': self.env['ir.sequence'].next_by_code('payment.order'),
            'user_id': self.env.user_id.id,
            'payment_mode_id': self.modo_pagamento.id,
            'partner_id': self.parceiro.id,
            'line_ids': self.account_move_line.id
        })

        self.fatura_cliente.payment_mode_id = self.modo_pagamento.id

    def test_gen_account_move_line(self):
        self.fatura_cliente.action_invoice_open()
        assert len(self.fatura_cliente.receivable_move_line_ids) == 1
        self.fatura_cliente.action_register_boleto()
        for move_line in self.fatura_cliente.receivable_move_line_ids:
            assert move_line.nosso_numero is not None
            assert move_line.boleto_emitido

    def test_gen_payment_order(self):
        self.fatura_cliente.action_invoice_open()
        self.fatura_cliente.action_register_boleto()
        self.acc_move_line = self.fatura_cliente.receivable_move_line_ids
        assert self.acc_move_line.partner_id == self.\
            account_move_line.partner_id
        #assert self.acc_move_line.journal_id == self.\
        #    account_move_line.journal_id
        #assert self.acc_move_line.account_id == self.\
        #    account_move_line.account_id
        #assert self.acc_move_line.debit == self.account_move_line.debit
        #assert self.acc_move_line.payment_mode_id == self.\
        #    account_move_line.payment_mode_id
        #assert self.acc_move_line.nosso_numero != self.\
        #    account_move_line.nosso_numero

    def test_gen_cnab(self):
        self.fatura_cliente.action_invoice_open()
        self.fatura_cliente.action_register_boleto()
        ordem_cobranca = self.env['payment.order'].search([
            ('line_ids', '=', self.fatura_cliente.receivable_move_line_ids.id)
        ], limit=1)
        ordem_cobranca.gerar_cnab()
        cnab = base64.decodestring(ordem_cobranca.cnab_file).split('\r\n')

        cnab_header_arquivo = cnab[0]
    #    cnab_header_lote = cnab[1]
        segmentos = cnab[2:-2]
    #    cnab_trailer_lote = cnab[-2]
    #    cnab_trailer_arquivo = cnab[-1]

        dict_segmentos = dict()
        dict_segmentos['P'] = []
        dict_segmentos['Q'] = []
        dict_segmentos['R'] = []
        for seg in segmentos:
            dict_segmentos[seg[13]] += [seg.replace('\r\n', '')]

        # Validação Header Arquivo
        assert cnab_header_arquivo[:3] == '756'
        assert cnab_header_arquivo[3:17] == '00000         '
        assert cnab_header_arquivo[17] in ('1', '2')
        assert cnab_header_arquivo[18:32] == re.sub(
            '[^0-9]', '', self.user_id.company_id.cnpj_cpf)
    #    assert cnab_header_arquivo[32:52] == (' ' * 20)
    #    assert cnab_header_arquivo[52:57] == self.modo_pagamento.\
    #        bank_account_id.bra_number.strip().zfill(5)
    #    assert cnab_header_arquivo[57] == self.modo_pagamento.\
    #        bank_account_id.bra_number_dig
    #    assert cnab_header_arquivo[58:70] == self.modo_pagamento.\
    #        bank_account_id.acc_number.zfill(12)
    #    assert cnab_header_arquivo[70] == self.modo_pagamento.\
    #        bank_account_id.acc_number_dig
    #    assert cnab_header_arquivo[71] == ' '
    #    assert cnab_header_arquivo[72:102] == self.user_id.company_id.\
    #        legal_name.ljust(30)
    #    assert cnab_header_arquivo[102:132] == 'SICOOB'.ljust(30)
    #    assert cnab_header_arquivo[132:142] == (' ' * 10)
    #    assert cnab_header_arquivo[142] == '1'
    #    assert cnab_header_arquivo[157:163] == str(ordem_cobranca.
    #                                               file_number).zfill(6)
    #    assert cnab_header_arquivo[163:166] == '087'
    #    assert cnab_header_arquivo[166:171] == ''.zfill(5)
    #    assert cnab_header_arquivo[171:].replace('\r\n', '') == ''.ljust(69)

        # Validação Header Lote
    #    assert cnab_header_lote[:3] == '756'
    #    assert cnab_header_lote[3:7] == '0001'
    #    assert cnab_header_lote[7] == '1'
    #    assert cnab_header_lote[8] == 'R'
    #    assert cnab_header_lote[9:11] == '01'
    #    assert cnab_header_lote[11:13] == '  '
    #    assert cnab_header_lote[13:16] == '040'
    #    assert cnab_header_lote[16] == ' '
    #    assert cnab_header_lote[17] in ('1', '2')
    #    assert cnab_header_lote[18:33] == re.sub(
    #        '[^0-9]', '', self.user_id.company_id.cnpj_cpf).zfill(15)
    #    assert cnab_header_lote[33:53] == (' ' * 20)
    #    assert cnab_header_lote[53:58] == self.modo_pagamento.\
    #        bank_account_id.bra_number.strip().zfill(5)
    #    assert cnab_header_lote[58] == self.modo_pagamento.bank_account_id.\
    #        bra_number_dig
    #    assert cnab_header_lote[59:71] == self.modo_pagamento.\
    #        bank_account_id.acc_number.zfill(12)
    #    assert cnab_header_lote[71] == self.modo_pagamento.\
    #        bank_account_id.acc_number_dig
    #    assert cnab_header_lote[72] == ' '
    #    assert cnab_header_lote[73:103] == self.user_id.company_id.\
    #        legal_name.ljust(30)
    #    assert cnab_header_lote[103:143] == (' ' * 40)
    #    assert cnab_header_lote[143:183] == (' ' * 40)
    #    assert cnab_header_lote[183:191] == str(self.ordem_cobranca.
    #                                            id).zfill(8)
    #    assert cnab_header_lote[199:207] == ''.zfill(8)
    #    assert cnab_header_lote[207:].replace('\r\n', '') == ''.ljust(33)

        # Validate Trailer Lote
    #    assert cnab_trailer_lote[:3] == '756'
    #    assert cnab_trailer_lote[3:7] == '0001'
    #    assert cnab_trailer_lote[7] == '5'
    #    assert cnab_trailer_lote[8:17] == ''.ljust(9)
    #    assert cnab_trailer_lote[18:23] == '5'.zfill(6)
    #    assert cnab_trailer_lote[115:123] == ''.ljust(8)
    #    assert cnab_trailer_lote[123:240] == ''.ljust(117)

        # Validate Trailer Arquivo
    #    assert cnab_trailer_arquivo[:3] == '756'
    #    assert cnab_trailer_arquivo[3:7] == '9' * 4
    #    assert cnab_trailer_arquivo[7] == '9'
    #    assert cnab_trailer_arquivo[8:17] == ''.ljust(9)
    #    assert cnab_trailer_arquivo[17:23] == '1'.zfill(6)
    #    assert cnab_trailer_arquivo[23:29] == '7'.zfill(6)
    #    assert cnab_trailer_arquivo[29:35] == ''.zfill(6)
    #    assert cnab_trailer_arquivo[35:240] == ''.ljust(205)
