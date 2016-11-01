# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestTaxBrasil(TransactionCase):

    def setUp(self):
        super(TestTaxBrasil, self).setUp()
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
            'amount': 0,
            'amount': 18,
            'price_include': False,
        })
        self.issqn = self.tax_model.create({
            'name': "ISSQN",
            'amount_type': 'division',
            'domain': 'issqn',
            'amount': 0,
            'amount': 5,
            'price_include': True,
        })
        self.ii = self.tax_model.create({
            'name': "II",
            'amount_type': 'division',
            'domain': 'ii',
            'amount': 0,
            'amount': 60,
            'price_include': True,
        })

    def test_simple_tax_pis_cofins(self):
        res = self.pis.compute_all(200.0)
        self.assertEquals(res['total_excluded'], 200.0)
        self.assertEquals(res['total_included'], 200.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 10.0)

        res = self.cofins.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 15.0)

    def test_ipi_tax(self):
        res = self.ipi.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 7.0)

        res = self.ipi.with_context(ipi_reducao_bc=10.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 106.3)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 6.3)

        res = self.ipi.with_context(
            ipi_reducao_bc=10.0, valor_frete=20).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.56)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 7.56)

        res = self.ipi.with_context(
            ipi_reducao_bc=10.0, valor_seguro=30).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 108.19)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 8.19)

        res = self.ipi.with_context(outras_despesas=30).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 109.1)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 9.1)

    def test_normal_icms(self):
        res = self.icms.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 17.0)

        res = self.icms.with_context(
            icms_aliquota_reducao_base=10.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 15.3)

        res = self.icms.with_context(
            icms_aliquota_reducao_base=10.0, valor_frete=5).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 16.065)

        res = self.icms.with_context(
            icms_aliquota_reducao_base=10.0, valor_seguro=8).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 16.524)

        res = self.icms.with_context(
            icms_aliquota_reducao_base=20.0,
            outras_despesas=20).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 16.32)

    def test_icms_st(self):
        res = self.icms_st.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 118.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 18.0)

    def test_icms_st_and_icms(self):
        taxes = self.icms | self.icms_st
        res = taxes.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 101.0)
        self.assertEquals(len(res['taxes']), 2)
        self.assertEquals(res['taxes'][0]['amount'], 1.0)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 17.0)  # ICMS

    def test_icms_with_ipi_base(self):
        taxes = self.ipi | self.icms
        res = taxes.with_context(incluir_ipi_base=True).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.0)
        self.assertEquals(len(res['taxes']), 2)
        self.assertEquals(res['taxes'][0]['amount'], 7.0)  # IPI
        self.assertEquals(res['taxes'][1]['amount'], 18.19)  # ICMS

    def test_icmsst_negativo(self):
        # ICMS ST que dá negativo deve retornar 0
        taxes = self.icms | self.icms_st
        res = taxes.with_context(
            icms_st_aliquota_reducao_base=50).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 2)

        self.assertEquals(res['taxes'][0]['amount'], 0.0)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 17.0)  # ICMS

    def test_icms_com_mva(self):
        # ICMS ST com aliquota de MVA
        taxes = self.icms | self.icms_st
        res = taxes.with_context(
            icms_st_aliquota_mva=35).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.3)
        self.assertEquals(len(res['taxes']), 2)

        self.assertEquals(res['taxes'][0]['amount'], 7.3)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 17.0)  # ICMS

    def test_icmsst_mva_reducao_base(self):
        # ICMS ST com aliquota de MVA e redução de base
        taxes = self.icms | self.icms_st
        res = taxes.with_context(
            icms_st_aliquota_mva=35,
            icms_st_aliquota_reducao_base=5.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 106.09)
        self.assertEquals(len(res['taxes']), 2)

        self.assertEquals(res['taxes'][0]['amount'], 6.09)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 17.0)  # ICMS

    def test_icmsst_mva_reducao_base_frete(self):
        # ICMS ST com aliquota de MVA e redução de base + frete
        taxes = self.icms | self.icms_st
        res = taxes.with_context(
            icms_st_aliquota_mva=35,
            icms_st_aliquota_reducao_base=5.0,
            valor_frete=15.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.0)
        self.assertEquals(len(res['taxes']), 2)
        self.assertEquals(res['taxes'][0]['amount'], 7.00)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 19.55)  # ICMS

    def test_icmsst_mva_reducao_seguro(self):
        # ICMS ST com aliquota de MVA e redução de base + seguro
        taxes = self.icms | self.icms_st
        res = taxes.with_context(
            icms_st_aliquota_mva=35,
            icms_st_aliquota_reducao_base=5.0,
            valor_seguro=25.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.61)
        self.assertEquals(len(res['taxes']), 2)
        self.assertEquals(res['taxes'][0]['amount'], 7.61)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 21.25)  # ICMS

    def test_icmsst_mva_reducao_despesa(self):
        # ICMS ST com aliquota de MVA e redução de base + despesas
        taxes = self.icms | self.icms_st
        res = taxes.with_context(
            icms_st_aliquota_mva=35,
            icms_st_aliquota_reducao_base=5.0,
            outras_despesas=30.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.91)
        self.assertEquals(len(res['taxes']), 2)

        self.assertEquals(res['taxes'][0]['amount'], 7.91)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 22.1)  # ICMS

    def test_tax_issqn(self):
        res = self.issqn.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 5.0)

    def test_tax_ii(self):
        res = self.ii.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 60.0)
