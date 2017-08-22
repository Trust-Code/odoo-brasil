# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestImportStatement(TransactionCase):

    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestImportStatement, self).setUp()
        self.journal = self.env['account.journal'].create({
            'name': 'Bank',
            'code': 'BNK',
            'type': 'bank',
            'bank_acc_number': '123',
            'currency_id': self.env.ref('base.BRL').id,
        })

        self.import_ofx = self.env['account.bank.statement.import'].create({
            'force_format': True,
            'file_format': 'ofx',
            'force_journal_account': True,
            'journal_id': self.journal.id,
            'data_file': base64.b64encode('000'),
        })

    def test_invalid_files(self):
        with self.assertRaises(UserError):
            self.import_ofx.import_file()

    def test_import_ofx_default(self):
        ofx = os.path.join(self.caminho, 'extratos/extrato.ofx')
        self.import_ofx.data_file = base64.b64encode(open(ofx, 'r').read())
        self.import_ofx.import_file()

        stmt = self.env['account.bank.statement'].search(
            [('journal_id', '=', self.journal.id)])

        lines = stmt.line_ids.sorted(lambda x: x.ref, reverse=True)
        self.assertTrue(stmt)
        self.assertEquals(len(lines), 28)
        self.assertEquals(lines[0].amount, -150.0)
        self.assertEquals(lines[0].name, u': SAQUE 24H 13563697')
        self.assertEquals(lines[0].ref, '20160926001')
        self.assertEquals(stmt.balance_start, 10.0)
        self.assertEquals(round(stmt.balance_end_real, 2), 914.45)
        self.assertEquals(stmt.balance_end, 914.45)

    def test_import_ofx_bb(self):
        ofx = os.path.join(self.caminho, 'extratos/extrato-bb.ofx')
        self.import_ofx.data_file = base64.b64encode(open(ofx, 'r').read())
        self.import_ofx.import_file()

        stmt = self.env['account.bank.statement'].search(
            [('journal_id', '=', self.journal.id)])

        lines = stmt.line_ids.sorted(lambda x: x.ref, reverse=True)
        self.assertTrue(stmt)
        self.assertEquals(len(lines), 26)
        self.assertEquals(lines[0].amount, -20.0)
        self.assertEquals(lines[0].name,
                          u': Telefone Pre-Pago - TIM - Sao Paulo')
        self.assertEquals(lines[0].ref, '20160908120000')
        self.assertEquals(stmt.balance_start, 172.61)
        self.assertEquals(round(stmt.balance_end_real, 2), 338.13)
        self.assertEquals(stmt.balance_end, 338.13)

    def test_import_ofx_itau(self):
        ofx = os.path.join(self.caminho, 'extratos/extrato-itau.ofx')
        self.import_ofx.data_file = base64.b64encode(open(ofx, 'r').read())
        self.import_ofx.import_file()

        stmt = self.env['account.bank.statement'].search(
            [('journal_id', '=', self.journal.id)])

        lines = stmt.line_ids.sorted(lambda x: x.ref, reverse=True)
        self.assertTrue(stmt)
        self.assertEquals(len(lines), 10)
        self.assertEquals(lines[0].amount, -240.33)
        self.assertEquals(lines[0].name, u': SISPAG FORNECEDORES')
        self.assertEquals(lines[0].ref, '20160810002')
        self.assertEquals(stmt.balance_start, -2690.0)
        self.assertEquals(round(stmt.balance_end_real, 2), -10081.58)
        self.assertEquals(stmt.balance_end, -10081.58)

    def test_import_ofx_without_force(self):
        ofx = os.path.join(self.caminho, 'extratos/extrato.ofx')
        self.import_ofx.data_file = base64.b64encode(open(ofx, 'r').read())
        self.import_ofx.force_format = False
        self.import_ofx.import_file()

        ofx = os.path.join(self.caminho, 'extratos/extrato-bb.ofx')
        self.import_ofx.data_file = base64.b64encode(open(ofx, 'r').read())
        self.import_ofx.force_format = False
        self.import_ofx.import_file()

        ofx = os.path.join(self.caminho, 'extratos/extrato-itau.ofx')
        self.import_ofx.data_file = base64.b64encode(open(ofx, 'r').read())
        self.import_ofx.force_format = False
        self.import_ofx.import_file()
