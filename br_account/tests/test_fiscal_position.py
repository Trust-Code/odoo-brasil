# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestFiscalPosition(TransactionCase):

    def setUp(self):
        super(TestFiscalPosition, self).setUp()

        self.main_company = self.env.ref('base.main_company')
        self.partner = self.env['res.partner'].create(dict(
            name='Parceiro Novo',
            is_company=False,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
        ))
        self.product = self.env['product.product'].create({
            'name': 'Normal Product',
            'default_code': '12',
            'list_price': 15.0
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda'
        })

        self.rule_icms = self.env['account.fiscal.position.tax.rule'].create({
            'name': 'Regra ICMS',
            'fiscal_position_id': self.fpos.id,
            'domain': 'icms',
            'cst_icms': '00',
            'reducao_icms': 20.0
        })

    def test_fiscal_mapping_extra(self):
        vals = self.fpos.map_tax_extra_values(
            self.main_company, self.product, self.partner)

        self.assertEquals(vals['icms_rule_id'].id, self.rule_icms.id)
        self.assertEquals(
            vals['icms_aliquota_reducao_base'], self.rule_icms.reducao_icms)
