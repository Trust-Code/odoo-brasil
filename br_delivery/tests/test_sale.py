from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')
        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })
        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
            'company_id': self.main_company.id,
        })
        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id
        })
        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture',
            'federal_nacional': 10.0,
            'estadual_imposto': 10.0,
            'municipal_imposto': 10.0,
            'cest': '123'
        })
        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'default_code': '25',
            'type': 'service',
            'fiscal_type': 'service',
            'service_type_id': self.env.ref(
                'br_data_account.service_type_101').id,
            'list_price': 50.0,
            'property_account_income_id': self.revenue_account.id,
        })
        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 15.0,
            'property_account_income_id': self.revenue_account.id,
        })
        default_partner = {
            'name': 'Nome Parceiro',
            'legal_name': 'Razão Social',
            'zip': '88037-240',
            'street': 'Endereço Rua',
            'number': '42',
            'district': 'Centro',
            'phone': '(48) 9801-6226',
            'property_account_receivable_id': self.receivable_account.id,
        }
        self.partner_fisica = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='545.770.154-98',
            company_type='person',
            is_company=False,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
            city_id=self.env.ref('br_base.city_4205407').id
        ))
        self.partner_juridica = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='05.075.837/0001-13',
            company_type='company',
            is_company=True,
            inscr_est='433.992.727',
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
            city_id=self.env.ref('br_base.city_4205407').id,
        ))
        self.tax_model = self.env['account.tax']
        self.pis = self.tax_model.create({
            'name': "PIS",
            'amount_type': 'division',
            'domain': 'pis',
            'amount': 5,
            'sequence': 1,
            'price_include': True,
        })
        self.cofins = self.tax_model.create({
            'name': "Cofins",
            'amount_type': 'division',
            'domain': 'cofins',
            'amount': 15,
            'sequence': 2,
            'price_include': True,
        })
        self.ipi = self.tax_model.create({
            'name': "IPI",
            'amount_type': 'percent',
            'domain': 'ipi',
            'amount': 7,
            'sequence': 3,
        })
        self.icms = self.tax_model.create({
            'name': "ICMS",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 17,
            'sequence': 4,
            'price_include': True,
        })
        self.icms_inter = self.tax_model.create({
            'name': "ICMS Inter",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 12,
            'sequence': 4,
            'price_include': True,
        })
        self.icms_st = self.tax_model.create({
            'name': "ICMS ST",
            'amount_type': 'icmsst',
            'domain': 'icmsst',
            'amount': 18,
            'price_include': False,
        })
        self.icms_difal_inter = self.tax_model.create({
            'name': "ICMS Difal Inter",
            'amount_type': 'division',
            'domain': 'icms_inter',
            'amount': 7,
            'price_include': True,
        })
        self.icms_difal_intra = self.tax_model.create({
            'name': "ICMS Difal Intra",
            'amount_type': 'division',
            'domain': 'icms_intra',
            'amount': 17,
            'price_include': True,
        })
        self.icms_fcp = self.tax_model.create({
            'name': "FCP",
            'amount_type': 'division',
            'domain': 'fcp',
            'amount': 2,
            'price_include': True,
        })
        self.issqn = self.tax_model.create({
            'name': "ISSQN",
            'amount_type': 'division',
            'domain': 'issqn',
            'amount': 5,
            'price_include': True,
        })
        self.ii = self.tax_model.create({
            'name': "II",
            'amount_type': 'division',
            'domain': 'ii',
            'amount': 60,
            'price_include': True,
        })
        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda'
        })
        order_line_data = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'product_uom': self.default_product.uom_id.id,
                    'product_uom_qty': 10.0,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'icms_cst_normal': '40',
                    'icms_csosn_simples': '102',
                    'ipi_cst': '50',
                    'pis_cst': '01',
                    'cofins_cst': '01',
                }
             ),
            (0, 0,
                {
                    'product_id': self.service.id,
                    'product_uom': self.service.uom_id.id,
                    'product_uom_qty': 10.0,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'pis_cst': '01',
                    'cofins_cst': '01',
                }
             )
        ]
        default_saleorder = {
            'fiscal_position_id': self.fpos.id,
            'order_line': order_line_data
        }

        self.sale_order = self.env['sale.order'].create(dict(
            default_saleorder.items(),
            name="SO 999",
            partner_id=self.partner_fisica.id
        ))

    def test_sale_order_to_invoice(self):
        self.sale_order.action_confirm()
        self.sale_order.action_invoice_create(final=True)
        self.assertEqual(len(self.sale_order.invoice_ids), 1)
