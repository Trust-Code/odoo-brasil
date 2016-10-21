# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.br_account.tests.test_br_account import TestTaxBrasil


class TestBrSale(TestTaxBrasil):

    def setUp(self):
        super(TestBrSale, self).setUp()
        self.products = {
            'prod_order': self.env.ref('product.product_order_01'),
            'prod_del': self.env.ref('product.product_delivery_01'),
            'serv_order': self.env.ref('product.service_order_01'),
            'serv_del': self.env.ref('product.service_delivery'),
        }
        self.partner = self.env.ref('base.res_partner_1')

    def test_sale_order_taxes(self):
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': p.name, 'product_id': p.id, 'product_uom_qty': 2,
                'product_uom': p.uom_id.id, 'price_unit': p.list_price}) for (_, p) in self.products.iteritems()],
            'pricelist_id': self.env.ref('product.list0').id,
        })
        self.assertEqual(so.amount_total, sum([2 * p.list_price for (k, p) in self.products.iteritems()]), 'Sale: total amount is wrong')
