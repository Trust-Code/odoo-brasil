# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestBaseBr(TransactionCase):

    def setUp(self):
        super(TestBaseBr, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')

        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture'
        })
        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 15.0
        })
        self.st_product = self.env['product.product'].create({
            'name': 'Product for ICMS ST',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 25.0
        })
        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'default_code': '25',
            'type': 'service',
            'fiscal_type': 'service',
            'list_price': 50.0
        })
        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })
        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id
        })

        self.tax_model = self.env['account.tax']
        self.pis_500 = self.tax_model.create({
            'name': "PIS",
            'amount_type': 'division',
            'domain': 'pis',
            'amount': 5,
            'sequence': 1,
            'price_include': True,
        })
        self.cofins_1500 = self.tax_model.create({
            'name': "Cofins",
            'amount_type': 'division',
            'domain': 'cofins',
            'amount': 15,
            'sequence': 2,
            'price_include': True,
        })
        self.ipi_700 = self.tax_model.create({
            'name': "IPI",
            'amount_type': 'percent',
            'domain': 'ipi',
            'amount': 7,
            'sequence': 3,
        })
        self.icms_1700 = self.tax_model.create({
            'name': "ICMS",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 17,
            'sequence': 4,
            'price_include': True,
        })
        self.icms_inter_1200 = self.tax_model.create({
            'name': "ICMS Inter",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 12,
            'sequence': 4,
            'price_include': True,
        })
        self.icms_st_1800 = self.tax_model.create({
            'name': "ICMS ST",
            'amount_type': 'icmsst',
            'domain': 'icmsst',
            'amount': 18,
            'price_include': False,
        })
        self.icms_st_1800_incluso = self.tax_model.create({
            'name': "ICMS ST Incluso",
            'amount_type': 'icmsst',
            'domain': 'icmsst',
            'amount': 18,
            'price_include': False,
            'icms_st_incluso': True,
        })
        self.icms_difal_inter_700 = self.tax_model.create({
            'name': "ICMS Difal Inter",
            'amount_type': 'division',
            'domain': 'icms_inter',
            'amount': 7,
            'price_include': True,
        })
        self.icms_difal_intra_1700 = self.tax_model.create({
            'name': "ICMS Difal Intra",
            'amount_type': 'division',
            'domain': 'icms_intra',
            'amount': 17,
            'price_include': True,
        })
        self.icms_difal_inter_1200 = self.tax_model.create({
            'name': "ICMS Difal Inter 12",
            'amount_type': 'division',
            'domain': 'icms_inter',
            'amount': 12,
            'price_include': True,
            'difal_por_dentro': True,
        })
        self.icms_difal_intra_1800 = self.tax_model.create({
            'name': "ICMS Difal Intra 18",
            'amount_type': 'division',
            'domain': 'icms_intra',
            'amount': 18,
            'price_include': True,
            'difal_por_dentro': True,
        })
        self.icms_fcp_200 = self.tax_model.create({
            'name': "FCP",
            'amount_type': 'division',
            'domain': 'fcp',
            'amount': 2,
            'price_include': True,
        })
        self.issqn_500 = self.tax_model.create({
            'name': "ISSQN",
            'amount_type': 'division',
            'domain': 'issqn',
            'amount': 5,
            'price_include': True,
        })
        self.ii_6000 = self.tax_model.create({
            'name': "II",
            'amount_type': 'division',
            'domain': 'ii',
            'amount': 60,
            'price_include': True,
        })
