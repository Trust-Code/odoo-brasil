# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.br_account.tests.test_base import TestBaseBr


class TestTaxBrasil(TestBaseBr):

    def test_simple_tax_pis_cofins(self):
        res = self.pis_500.compute_all(200.0)
        self.assertEquals(res['total_excluded'], 200.0)
        self.assertEquals(res['total_included'], 200.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 10.0)

        res = self.cofins_1500.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 15.0)

    def test_ipi_tax(self):
        res = self.ipi_700.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 7.0)

        res = self.ipi_700.with_context(ipi_reducao_bc=10.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 106.3)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 6.3)

        res = self.ipi_700.with_context(
            ipi_reducao_bc=10.0, valor_frete=20).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.56)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 7.56)

        res = self.ipi_700.with_context(
            ipi_reducao_bc=10.0, valor_seguro=30).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 108.19)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 8.19)

        res = self.ipi_700.with_context(outras_despesas=30).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 109.1)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 9.1)

    def test_normal_icms(self):
        res = self.icms_1700.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 17.0)

        res = self.icms_1700.with_context(
            icms_aliquota_reducao_base=10.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 15.3)

        res = self.icms_1700.with_context(
            icms_aliquota_reducao_base=10.0, valor_frete=5).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 16.065)

        res = self.icms_1700.with_context(
            icms_aliquota_reducao_base=10.0, valor_seguro=8).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 16.524)

        res = self.icms_1700.with_context(
            icms_aliquota_reducao_base=20.0,
            outras_despesas=20).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 16.32)

    def test_icms_st(self):
        res = self.icms_st_1800.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 118.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 18.0)

    def test_icms_st_and_icms(self):
        taxes = self.icms_1700 | self.icms_st_1800
        res = taxes.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 101.0)
        self.assertEquals(len(res['taxes']), 2)
        self.assertEquals(res['taxes'][0]['amount'], 1.0)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 17.0)  # ICMS

    def test_icms_with_ipi_base(self):
        taxes = self.ipi_700 | self.icms_1700
        res = taxes.with_context(incluir_ipi_base=True).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.0)
        self.assertEquals(len(res['taxes']), 2)
        self.assertEquals(res['taxes'][0]['amount'], 7.0)  # IPI
        self.assertEquals(res['taxes'][1]['amount'], 18.19)  # ICMS

    def test_icmsst_negativo(self):
        # ICMS ST que dá negativo deve retornar 0
        taxes = self.icms_1700 | self.icms_st_1800
        res = taxes.with_context(
            icms_st_aliquota_reducao_base=50).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 2)

        self.assertEquals(res['taxes'][0]['amount'], 0.0)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 17.0)  # ICMS

    def test_icms_com_mva(self):
        # ICMS ST com aliquota de MVA
        taxes = self.icms_1700 | self.icms_st_1800
        res = taxes.with_context(
            icms_st_aliquota_mva=35).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 107.3)
        self.assertEquals(len(res['taxes']), 2)

        self.assertEquals(res['taxes'][0]['amount'], 7.3)  # ICMS ST
        self.assertEquals(res['taxes'][1]['amount'], 17.0)  # ICMS

    def test_icmsst_mva_reducao_base(self):
        # ICMS ST com aliquota de MVA e redução de base
        taxes = self.icms_1700 | self.icms_st_1800
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
        taxes = self.icms_1700 | self.icms_st_1800
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
        taxes = self.icms_1700 | self.icms_st_1800
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
        taxes = self.icms_1700 | self.icms_st_1800
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
        res = self.issqn_500.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 5.0)

    def test_tax_ii(self):
        res = self.ii_6000.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 60.0)

    def test_difal_incomplete(self):
        res = self.icms_difal_inter_700.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 0)

        res = self.icms_difal_intra_1700.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 0)

        res = self.icms_fcp_200.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 0)

    def test_tax_difal(self):
        taxes = self.icms_difal_inter_700 | self.icms_difal_intra_1700
        res = taxes.with_context(icms_aliquota_inter_part=30)\
            .compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 2)
        self.assertEquals(res['taxes'][0]['amount'], 7.0)  # Remetente
        self.assertEquals(res['taxes'][1]['amount'], 3.0)  # Destinatário

    def test_tax_difal_por_dentro(self):
        taxes = self.icms_difal_inter_1200 | self.icms_difal_intra_1800
        res = taxes.with_context(icms_aliquota_inter_part=30)\
            .compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 2)
        self.assertEquals(res['taxes'][0]['amount'], 5.12)  # Remetente
        self.assertEquals(res['taxes'][1]['amount'], 2.2)  # Destinatário

    def test_difal_fcp(self):
        taxes = self.icms_difal_inter_700 | self.icms_difal_intra_1700 | \
            self.icms_fcp_200
        res = taxes.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 3)
        self.assertEquals(res['taxes'][0]['amount'], 2.0)  # Remetente
        self.assertEquals(res['taxes'][1]['amount'], 8.0)  # Destinatário
        self.assertEquals(res['taxes'][2]['amount'], 2.0)  # FCP

    def test_difal_fcp_reducao_frete_seguro_despesas(self):
        taxes = self.icms_difal_inter_700 | self.icms_difal_intra_1700 | \
            self.icms_fcp_200
        res = taxes.with_context(
            icms_aliquota_reducao_base=20,
            valor_frete=5.0, outras_despesas=5.0,
            valor_seguro=30.0).compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 100.0)
        self.assertEquals(len(res['taxes']), 3)
        self.assertEquals(res['taxes'][0]['amount'], 2.24)  # Remetente
        self.assertEquals(res['taxes'][1]['amount'], 8.96)  # Destinatário
        self.assertEquals(res['taxes'][2]['amount'], 2.24)  # FCP
