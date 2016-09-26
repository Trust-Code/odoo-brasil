# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from datetime import date


class TestCnab(TransactionCase):
    """Tests the generation of CNAB files against the each bank manual"""

    def setUp(self):
        super(TransactionCase, self).setUp()
        self.product_tmpl_model = self.env['product.template']
        self.account_receivable = self.env['account.account'].create({
            'name': 'Conta Recebível', 'code': '0.0.0.0.0', 'user_type_id': 1,
            })
        self.account_payable = self.env['account.account'].create({
            'name': 'Conta Pagável', 'code': '1.1.1.1.1', 'user_type_id': 2,
            })
        self.account_outra = self.env['account.account'].create({
            'name': 'Conta Bens Disp.', 'code': '2.2.2.2.2', 'user_type_id': 5,
            })
        self.produto = self.product_tmpl_model.create({
            'name': 'Produto', 'default_code': '1', 'list_price': 10.00, })
        self.parceiro = self.env['res.partner'].create({
            'name': 'Catarina Isabella Nascimento',
            'cnpj_cpf': '60520426991', 'zip': '85507300',
            'street': 'Rua Princesa Isabel', 'number': '936',
            'district': 'Morumbi', 'country_id': 32, 'state_id': 86,
            'city_id': 3521, 'phone': '(46) 3695-7760',
            'mobile': '(46) 8284-4788',
            'property_account_receivable_id': self.account_receivable.id,
            'property_account_payable_id': self.account_payable.id,
        })
        self.linha_fatura = self.env['account.invoice.line'].create({
            'product_id': self.produto.id, 'account_id': self.account_outra.id,
            'icms_cst': '00', 'ipi_cst': '99', 'pis_cst': '99',
            'cofins_cst': '99'
        })
        self.fatura_cliente = self.env['account.invoice'].create({
            'partner_id': self.parceiro.id,
            'date_invoice': date.today(),
            'invoice_line_ids': self.linha_fatura.id,
            'account_id': self.account_receivable.id,
        })

        self.account_journal_model = self.env['account.journal'].create({
            'name': 'Diário Teste', 'type': 'sale', 'code': 'DTJr', })
