# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase
from odoo.tools import float_compare


class TestTaxBrasil(TransactionCase):

    def setUp(self):
        super(TestTaxBrasil, self).setUp()

        self.pis = self.tax_model.create({
            'name': "PIS",
            'amount_type': 'division',
            'amount': 5,
            'sequence': 1,
            'price_include': True,
        })
        self.cofins = self.tax_model.create({
            'name': "Cofins",
            'amount_type': 'division',
            'amount': 15,
            'sequence': 2,
            'price_include': True,
        })
        self.ipi = self.tax_model.create({
            'name': "IPI",
            'amount_type': 'percent',
            'amount': 7,
            'sequence': 3,
        })
        self.icms = self.tax_model.create({
            'name': "ICMS",
            'amount_type': 'division',
            'amount': 17,
            'sequence': 4,
            'price_include': True,
        })
        self.icms_inter = self.tax_model.create({
            'name': "ICMS Inter",
            'amount_type': 'division',
            'amount': 12,
            'sequence': 4,
            'price_include': True,
        })
        self.icms_st = self.tax_model.create({
            'name': "ICMS ST",
            'amount_type': 'icmsst',
            'amount': 0,
            'amount': 18,
            'price_include': False,
        })

    def test_simple_tax_pis_cofins(self):
        res = self.pis.compute_all(200.0)
        self.assertEquals(res['total_excluded'], 200.0)
        self.assertEquals(res['total_included'], 210.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 10.0)

        res = self.cofins.compute_all(100.0)
        self.assertEquals(res['total_excluded'], 100.0)
        self.assertEquals(res['total_included'], 105.0)
        self.assertEquals(len(res['taxes']), 1)
        self.assertEquals(res['taxes'][0]['amount'], 5.0)
