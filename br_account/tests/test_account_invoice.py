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
                    'ii_base_calculo': 150.00,
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

    def test_invoice_pis_cofins_taxes(self):
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
                item._onchange_product_id()
                self.assertEquals(item.pis_base_calculo, item.price_total)
                self.assertEquals(item.pis_aliquota, 5.0)
                self.assertEquals(item.pis_valor, item.price_total * 0.05)

                item.tax_cofins_id = self.cofins_1500
                item._onchange_tax_cofins_id()
                item._onchange_product_id()
                self.assertEquals(item.cofins_base_calculo, item.price_total)
                self.assertEquals(item.cofins_aliquota, 15.0)
                self.assertEquals(item.cofins_valor, item.price_total * 0.15)

                self.assertEquals(len(item.invoice_line_tax_ids), 2)

            self.assertEquals(invoice.pis_base, 650.0)
            self.assertEquals(invoice.cofins_base, 650.0)
            self.assertEquals(invoice.pis_value, 32.5)
            self.assertEquals(invoice.cofins_value, 97.5)

            # Valido a fatura
            invoice.action_invoice_open()

            # Ainda deve ter os mesmos valores
            self.assertEquals(invoice.pis_base, 650.0)
            self.assertEquals(invoice.cofins_base, 650.0)
            self.assertEquals(invoice.pis_value, 32.5)
            self.assertEquals(invoice.cofins_value, 97.5)

    def test_invoice_issqn_and_ii_taxes(self):
        for invoice in self.invoices:

            prod_item = invoice.invoice_line_ids[0]
            serv_item = invoice.invoice_line_ids[1]

            # II
            prod_item.tax_ii_id = self.ii_6000
            prod_item._onchange_tax_ii_id()
            self.assertEquals(prod_item.price_total, 150.0)
            self.assertEquals(prod_item.ii_base_calculo, 150.0)
            self.assertEquals(prod_item.ii_valor, 90.0)
            self.assertEquals(prod_item.ii_aliquota, 60.0)

            # ISSQN
            serv_item.tax_issqn_id = self.issqn_500
            serv_item._onchange_tax_issqn_id()
            self.assertEquals(serv_item.price_total, 500.0)
            self.assertEquals(serv_item.issqn_base_calculo, 500.0)
            self.assertEquals(serv_item.issqn_valor, 25.0)
            self.assertEquals(serv_item.issqn_aliquota, 5.0)

            # Totais
            self.assertEquals(invoice.issqn_base, 500.0)
            self.assertEquals(invoice.ii_value, 90.0)
            self.assertEquals(invoice.issqn_value, 25.0)

            # Valido a fatura
            invoice.action_invoice_open()

            # Ainda deve ter os mesmos valores
            self.assertEquals(invoice.issqn_base, 500.0)
            self.assertEquals(invoice.ii_value, 90.0)
            self.assertEquals(invoice.issqn_value, 25.0)

    def test_invoice_icms_normal_tax(self):
        for invoice in self.invoices:

            first_item = invoice.invoice_line_ids[0]

            # ICMS
            first_item.tax_icms_id = self.icms_1700
            first_item._onchange_tax_icms_id()
            self.assertEquals(first_item.price_total, 150.0)
            self.assertEquals(first_item.icms_base_calculo, 150.0)
            self.assertEquals(first_item.icms_valor, 25.5)
            self.assertEquals(first_item.icms_aliquota, 17.0)

            for item in invoice.invoice_line_ids:
                item.tax_icms_id = self.icms_1700
                item._onchange_tax_icms_id()
                item._onchange_product_id()
                self.assertEquals(item.icms_base_calculo, item.price_total)
                self.assertEquals(
                    item.icms_valor, round(item.price_total * 0.17, 2))
                self.assertEquals(item.icms_aliquota, 17.0)

                self.assertEquals(len(item.invoice_line_tax_ids), 1)

            self.assertEquals(invoice.icms_base, 650.0)
            self.assertEquals(invoice.icms_value, 110.5)

            # Valido a fatura
            invoice.action_invoice_open()

            # Ainda deve ter os mesmos valores
            self.assertEquals(invoice.icms_base, 650.0)
            self.assertEquals(invoice.icms_value, 110.5)

    def test_invoice_icms_reducao_base_tax(self):
        for invoice in self.invoices:

            first_item = invoice.invoice_line_ids[0]

            # ICMS com Redução de base
            first_item.tax_icms_id = self.icms_1700
            first_item.icms_aliquota_reducao_base = 10.0
            first_item._onchange_tax_icms_id()
            self.assertEquals(first_item.price_total, 150.0)
            self.assertEquals(first_item.icms_base_calculo, 135.0)
            self.assertEquals(first_item.icms_valor, 22.95)
            self.assertEquals(first_item.icms_aliquota, 17.0)

            for item in invoice.invoice_line_ids:
                item.tax_icms_id = self.icms_1700
                item.icms_aliquota_reducao_base = 10.0
                item._onchange_tax_icms_id()
                item._onchange_product_id()
                self.assertEquals(
                    item.icms_base_calculo, round(item.price_total * 0.9, 2))
                self.assertEquals(
                    item.icms_valor, round(item.price_total * 0.9 * 0.17, 2))
                self.assertEquals(item.icms_aliquota, 17.0)

                self.assertEquals(len(item.invoice_line_tax_ids), 1)

            self.assertEquals(invoice.icms_base, 585.0)
            self.assertEquals(invoice.icms_value, 99.45)

            # Valido a fatura
            invoice.action_invoice_open()

            # Ainda deve ter os mesmos valores
            self.assertEquals(invoice.icms_base, 585.0)
            self.assertEquals(invoice.icms_value, 99.45)
