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

        self.cnab_imp = self.env['account.bank.statement.import'].with_context(
            journal_id=self.journal.id).create({
                'force_format': True,
                'file_format': 'cnab240',
                'force_journal_account': True,
                'journal_id': self.journal.id,
                'data_file': base64.b64encode('000'),
            })

    def test_invalid_files(self):
        with self.assertRaises(UserError):
            self.cnab_imp.import_file()

    def test_import_cnab_default(self):
        cnab = os.path.join(self.caminho, 'extratos/CNAB240-Sicoob.ret')
        self.cnab_imp.data_file = base64.b64encode(open(cnab, 'r').read())
        # Sicoob
        self.journal.bank_id = self.env.ref('br_data_base.res_bank_115').id
        self.cnab_imp.import_file()

        stmt = self.env['account.bank.statement'].search(
            [('journal_id', '=', self.journal.id)])

        lines = stmt.line_ids.sorted(lambda x: x.ref, reverse=True)
        self.assertTrue(stmt)
        self.assertEquals(len(lines), 3)
        self.assertEquals(lines[0].amount, 260.0)
        self.assertEquals(
            lines[0].name,
            u'Empresa de teste limitada me          00 : NF-0117/01')
        self.assertEquals(lines[0].ref, 'NF-0117/01')
        self.assertEquals(stmt.balance_start, 0.0)
        self.assertEquals(stmt.balance_end_real, 2405.6)
        self.assertEquals(stmt.balance_end, 2405.6)

    def test_import_cnab_without_force(self):
        cnab = os.path.join(self.caminho, 'extratos/CNAB240-Sicoob.ret')
        self.cnab_imp.data_file = base64.b64encode(open(cnab, 'r').read())
        self.cnab_imp.force_format = False
        # Sicoob
        self.journal.bank_id = self.env.ref('br_data_base.res_bank_115').id
        self.cnab_imp.import_file()
        stmt = self.env['account.bank.statement'].search(
            [('journal_id', '=', self.journal.id)])
        self.assertTrue(stmt)
        self.assertEquals(len(stmt.line_ids), 3)
