# -*- coding: utf-8 -*-
# © 2018 Marina Domingues, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestBrCnabPayment(TransactionCase):

    def setUp(self):
        super(TestBrCnabPayment, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')
        self.main_company.write({
            'name': 'Trustcode',
            'legal_name': 'Trustcode Tecnologia da Informação',
            'cnpj_cpf': '92.743.275/0001-33',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
        })
        self.main_company.write({'inscr_est': '219.882.606'})
        self.payable_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Despesas com Fornecedores',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })
        self.expense_account = self.env['account.account'].create({
            'code': '2.0.0',
            'name': 'Despesas a pagar',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })
        sicoob = self.env['res.bank'].search([('bic', '=', '756')])
        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture',
            'federal_nacional': 10.0,
            'estadual_imposto': 10.0,
            'municipal_imposto': 10.0,
            'cest': '123'
        })
        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'default_code': '12',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 15.0
        })
        self.partner_fisica = self.env['res.partner'].create(dict(
            name='Parceiro',
            company_type='person',
            is_company=False,
            street='Donicia',
            zip='88032-050',
            cnpj_cpf='066.212.049-30',
            district='Centro',
            number=45,
            # property_account_receivable_id=self.receivable_account.id,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
            city_id=self.env.ref('br_base.city_4205407').id,
        ))
        self.receivable_account = self.env['res.partner.bank'].create({
            'acc_number': '12345',  # 5 digitos
            'acc_number_dig': '0',  # 1 digito
            'bra_number': '1234',  # 4 digitos
            'bra_number_dig': '0',
            'codigo_convenio': '123456-6',  # 7 digitos
            'bank_id': sicoob.id,
            'partner_id': self.partner_fisica.id,
        })
        self.user = self.env['res.users'].create({
            'name': 'trustcode',
            'login': 'trust'
        })
        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'NF',
            'type': 'sale',
            'default_debit_account_id': self.payable_account.id,
            'default_credit_account_id': self.payable_account.id,
        })

    def test_ordenate_lines(self):
        pass  # TODO
