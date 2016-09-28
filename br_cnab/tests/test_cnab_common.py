# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from datetime import date


class TestCnab(TransactionCase):
    """Tests the generation of CNAB files against the each bank manual"""

    def setUp(self):
        super(TestCnab, self).setUp()
        self.produto = self.env['product.product'].create({
            'name': 'Produto', 'default_code': '1', 'list_price': 10.00, })

        self.parceiro = self.env['res.partner'].create({
            'name': 'Catarina Isabella Nascimento',
            'cnpj_cpf': '60520426991', 'zip': '85507300',
            'street': 'Rua Princesa Isabel', 'number': '936',
            'district': 'Morumbi', 'country_id': 32, 'state_id': 86,
            'city_id': 3521, 'phone': '(46) 3695-7760',
            'mobile': '(46) 8284-4788',
        })
        invoice_lines = [(0, 0, {
            'product_id': self.produto.id,
            'account_id': self.env['account.account'].search(
                [('user_type_id', '=', self.env.ref(
                    'account.data_account_type_revenue').id)], limit=1).id,
            'icms_cst': '00', 'ipi_cst': '99', 'pis_cst': '99',
            'cofins_cst': '99', 'price_unit': self.produto.list_price,
            'name': self.produto.name
        })]
        self.journalrec = self.env['account.journal'].search(
            [('type', '=', 'sale')])[0]
        self.fatura_cliente = self.env['account.invoice'].create({
            'partner_id': self.parceiro.id,
            'date_invoice': date.today(),
            'invoice_line_ids': invoice_lines,
            'account_id': self.parceiro.property_account_receivable_id.id,
            'journal_id': self.journalrec.id,
        })
        self.company_id = self.env.user.company_id
        self.company_id.legal_name = "Nome Fictício"
        self.company_id.cnpj_cpf = "81228576000102"
