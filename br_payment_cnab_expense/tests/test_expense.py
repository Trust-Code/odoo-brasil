# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestHrExpense(TransactionCase):

    def setUp(self):
        super(TestHrExpense, self).setUp()

        self.product = self.env.ref('hr_expense.air_ticket')
        self.employee = self.env.ref('hr.employee_mit')
        self.company = self.env.ref('base.main_company')

        # Create payable account for the expense
        user_type = self.env.ref('account.data_account_type_payable')
        account_payable = self.env['account.account'].create({
            'code': 'X1111',
            'name': 'HR Expense - Test Payable Account',
            'user_type_id': user_type.id,
            'reconcile': True
        })
        self.home_address_id = self.employee.address_home_id
        self.home_address_id.property_account_payable_id = account_payable.id

        # Create expenses account for the expense
        user_type = self.env.ref('account.data_account_type_expenses')
        account_expense = self.env['account.account'].create({
            'code': 'X2120',
            'name': 'HR Expense - Test Purchase Account',
            'user_type_id': user_type.id
        })
        # Assign it to the air ticket product
        self.product.write({'property_account_expense_id': account_expense.id})

        # Create Sales Journal
        company = self.env.ref('base.main_company')
        self.journal_id = self.env['account.journal'].create({
            'name': 'Purchase Journal - Test',
            'code': 'HRTPJ',
            'type': 'purchase',
            'company_id': company.id
        })

        self.expense = self.env['hr.expense.sheet'].create({
            'name': 'Despesa com Reembolso e transferência via TED',
            'employee_id': self.employee.id,
        })
        self.expense_line = self.env['hr.expense'].create({
            'name': 'Despesa de Deslocamento',
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'unit_amount': 700.00,
            'sheet_id': self.expense.id,
        })
        self.ted_payment = self.env['l10n_br.payment.mode'].create({
            'name': 'Transferência (TED)',
            'company_id': self.company.id,
            'type': 'payable',
            'payment_type': '01',
            # 'journal_id': ,
            'service_type': '60',
            'move_finality': '01',
        })

    def test_expense_reimburse_cnab(self):
        self.expense_line.payment_mode = 'own_account'
        self.expense.approve_expense_sheets()
        self.expense.payment_mode_id = self.ted_payment.id
        self.expense.date_payment = '2019-05-26'
        # Lança a despesa.
        self.expense.action_sheet_move_create()
