# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestImportIBPT(TransactionCase):

    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestImportIBPT, self).setUp()
        self.wiz = self.env['product.fiscal.classification.wizard'].create({
            'ncm_csv_delimiter': ';',
            'has_quote_char': True,
        })

    def test_import_table_ibpt(self):
        with self.assertRaises(UserError):
            self.wiz.import_ncm()

        self.wiz.product_fiscal_class_csv = base64.b64encode(open(
            os.path.join(self.caminho, 'csv/tabela-ibpt.csv'), 'rb').read())

        with self.assertRaises(UserError):
            self.wiz.import_ncm()

        self.wiz.has_quote_char = False
        self.wiz.import_ncm()
