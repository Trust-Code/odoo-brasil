# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import TransactionCase


class TestCieloIntegration(TransactionCase):

    def setUp(self):
        super(TestCieloIntegration, self).setUp()

    def test_cielo_notification(self):
        post = {}
        post["order_number"] = "SO030"
        post["amount"] = "2100"
        post["discount_amount"] = "0"
        post["checkout_cielo_order_number"] = \
            "f11ff6f582f0468f8063d9d716c55e25"
        post["created_date"] = "24/11/2016 16:46:37"
        post["customer_name"] = "Trustcode Suporte"
        post["customer_phone"] = "4898016226"
        post["customer_identity"] = "06621204930"
        post["customer_email"] = "admin@example.com"
        post["shipping_type"] = "5"
        post["shipping_price"] = "0"
        post["payment_method_type"] = "1"
        post["payment_method_brand"] = "1"
        post["payment_maskedcreditcard"] = "401200******3335"
        post["payment_installments"] = "1"
        post["payment_status"] = "3"
        post["tid"] = "241120161646374098"
        post["test_transaction"] = "True"
        return post

    def test_change_status(self):
        post = {}
        post["checkout_cielo_order_number"] = \
            "01eae1656d59445ab34c9dcfee0db37e"
        post["amount"] = "2100"
        post["order_number"] = "SO030"
        post["payment_status"] = "2"
        post["test_transaction"] = "True"
        return post
