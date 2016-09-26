# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

#  from odoo.exceptions import UserError, AccessError
from .test_cnab_common import TestCnab
from random import randint


class TestCnabSicoob(TestCnab):

    def setUp(self):
        super(TestCnab, self).setUp()
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
            'boleto_type': 9, 'payment_type_id': self.tipo_pagamento.id,
            'boleto_carteira': '1', 'boleto_modalidade': '01',
            'instrucoes': "Lorem ipsum dolor sit amet, consectetur adipiscing \
elit. Etiam interdum.", })

        self.account_move_line = self.env['account.move.line'].create({
            'name': str(self.env['ir.sequence'].
                        next_by_code('doc.number.cnab')),
            'partner_id': self.parceiro.id,
            'journal_id': self.account_journal_model.id,
            'account_id': self.account_receivable.id,
            'debit': self.produto.list_price,
            'payment_mode_id': self.modo_pagamento.id,
        })

        self.ordem_cobranca = self.env['payment.order'].create({
            'name': self.env['ir.sequence'].next_by_code('payment.order'),
            'user_id': self.env.user_id.id,
            'payment_mode_id': self.modo_pagamento.id,
            'partner_id': self.parceiro.id,
        })

        self.fatura_cliente.payment_mode_id = self.modo_pagamento.id

    def test_gen_account_move_line(self):
        self.fatura_cliente.action_invoice_open()
        assert len(self.fatura_cliente.receivable_move_line_ids, 1)
        self.fatura_cliente.action_register_boleto()
        for move_line in self.fatura_cliente.receivable_move_line_ids:
            assert move_line.nosso_numero
            assert move_line.boleto_emitido

    def test_gen_payment_order(self):
        self.fatura_cliente.action_invoice_open()
        self.fatura_cliente.action_register_boleto()
        self.acc_move_line = self.env['account.move.line'].search([])
        ordem_cobranca_gerada = self.env['payment.order'].search([], limit=1)
        #  self.ordem_cobranca.line_ids =
