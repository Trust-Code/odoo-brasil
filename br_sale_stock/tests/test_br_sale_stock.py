# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from mock import patch
from odoo.addons.sale.tests.test_sale_common import TestSale


class TestBrSaleStock(TestSale):

    @patch('odoo.addons.br_localization_filtering.models.br_localization_filtering.BrLocalizationFiltering._is_user_br_localization')  # noqa  java feelings
    def test_sale_order_ratio_expenses(self, br_localization):
        """ Test the sale order new fields
            - Invoice repeatedly while varrying delivered quantities and
            check that invoice are always what we expect
        """
        br_localization.return_value = True
        product = self.env.ref('product.product_order_01')
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'total_despesas': 5.0,
            'order_line': [(0, 0, {
                'name': product.name, 'product_id': product.id,
                'product_uom_qty': 2, 'product_uom': product.uom_id.id,
                'price_unit': 10.0})],
            'pricelist_id': self.env.ref('product.list0').id,
        })
        self.assertEqual(so.amount_total, 25.0, 'Sale: total amount is wrong')
