# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.br_account.tests.test_base import TestBaseBr


class TestAccountInvoice(TestBaseBr):

    def setUp(self):
        super(TestAccountInvoice, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Nome Parceiro',
            'is_company': False,
            'property_account_receivable_id': self.receivable_account.id,
        })
        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })
        invoice_line_data = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'quantity': 10.0,
                    'price_unit': self.default_product.list_price,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                }
             ),
            (0, 0,
                {
                    'product_id': self.service.id,
                    'quantity': 10.0,
                    'price_unit': self.service.list_price,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    'product_type': self.service.fiscal_type,
                }
             )
        ]
        default_invoice = {
            'name': u"Teste Validação",
            'reference_type': "none",
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'invoice_line_ids': invoice_line_data
        }
        self.invoices = self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner.id
        ))

    def test_compute_total_values(self):
        for invoice in self.invoices:
            self.assertEquals(invoice.amount_total, 650.0)
            self.assertEquals(invoice.amount_total_signed, 650.0)
            self.assertEquals(invoice.amount_untaxed, 650.0)
            self.assertEquals(invoice.amount_tax, 0.0)
            self.assertEquals(invoice.total_tax, 0.0)

            # Verifico as linhas recebiveis
            self.assertEquals(len(invoice.receivable_move_line_ids), 0)

            # Valido a fatura
            invoice.action_invoice_open()

            # Verifico as linhas recebiveis
            self.assertEquals(len(invoice.receivable_move_line_ids), 1)

    def test_invoice_simple_taxes(self):
        for invoice in self.invoices:

            first_item = invoice.invoice_line_ids[0]

            # PIS
            first_item.tax_pis_id = self.pis_500
            first_item._onchange_tax_pis_id()
            self.assertEquals(first_item.price_total, 150.0)
            self.assertEquals(first_item.pis_base_calculo, 150.0)
            self.assertEquals(first_item.pis_valor, 7.5)
            self.assertEquals(first_item.pis_aliquota, 5.0)

            # COFINS
            first_item.tax_cofins_id = self.cofins_1500
            first_item._onchange_tax_cofins_id()
            self.assertEquals(first_item.price_total, 150.0)
            self.assertEquals(first_item.cofins_base_calculo, 150.0)
            self.assertEquals(first_item.cofins_valor, 22.5)
            self.assertEquals(first_item.cofins_aliquota, 15.0)

            for item in invoice.invoice_line_ids:
                item.tax_pis_id = self.pis_500
                item._onchange_tax_pis_id()
                self.assertEquals(item.pis_base_calculo, item.price_total)
                self.assertEquals(item.pis_aliquota, 5.0)
                self.assertEquals(item.pis_valor, item.price_total * 0.05)

                item.tax_cofins_id = self.cofins_1500
                item._onchange_tax_cofins_id()
                self.assertEquals(item.cofins_base_calculo, item.price_total)
                self.assertEquals(item.cofins_aliquota, 15.0)
                self.assertEquals(item.cofins_valor, item.price_total * 0.15)

            self.assertEquals(invoice.pis_base, 650.0)
            self.assertEquals(invoice.cofins_base, 650.0)
            self.assertEquals(invoice.pis_value, 32.5)
            self.assertEquals(invoice.cofins_value, 97.5)
