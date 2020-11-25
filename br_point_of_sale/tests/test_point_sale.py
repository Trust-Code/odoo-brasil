# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
from datetime import datetime
from odoo.tests.common import TransactionCase


class TestPointSaleBR(TransactionCase):

    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestPointSaleBR, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.currency_real = self.env.ref('base.BRL')
        self.main_company.write({
            'name': 'Trustcode',
            'legal_name': 'Trustcode Tecnologia da Informação',
            'cnpj_cpf': '92.743.275/0001-33',
            'inscr_est': '219.882.606',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
            'currency_id': self.currency_real.id,
            'nfe_a1_password': '123456',
            'nfe_a1_file': base64.b64encode(
                open(os.path.join(self.caminho, 'teste.pfx'), 'r').read()),
        })

        # NCM
        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture',
            'federal_nacional': 10.0,
            'estadual_imposto': 10.0,
            'municipal_imposto': 10.0,
            'cest': '123'
        })
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # PRODUTOS
        self.product_a = self.env['product.product'].create({
            'name': 'PRODUTO A',
            'list_price': 10.00,
            'default_code': '1',
            'fiscal_classification_id': self.default_ncm.id,
        })
        self.product_b = self.env['product.product'].create({
            'name': 'PRODUTO B',
            'list_price': 5.00,
            'default_code': '2',
            'fiscal_classification_id': self.default_ncm.id,
        })
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # CONTAS
        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })
        self.receivable_acc = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id
        })
        field = self.env['ir.model.fields'].search([
            ('name', '=', 'property_account_receivable_id'),
            ('model_id.model', '=', 'res.partner')])

        self.env['ir.property'].create({
            'name': 'property_account_receivable_id',
            'type': 'many2one',
            'fields_id': field.id,
            'value_reference': 'account.account,%d' % self.receivable_acc.id,
        })

        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # JOURNAIS CONTABEIS
        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.receivable_acc.id,
        })
        self.journalpos = self.env['account.journal'].create({
            'name': 'POS SALE JOURNAL',
            'code': 'POSS',
            'type': 'sale',
        })
        cash_journal = [
            (0, 0,
                {
                    'name': 'CASH',
                    'code': 'CASH',
                    'type': 'cash',
                    'metodo_pagamento': '01',
                    'default_debit_account_id': self.revenue_account.id,
                    'default_credit_account_id': self.receivable_acc.id,
                })]
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # IMPOSTOS - PIS, COFINS E ICMS(COM E SEM REDUCAO)
        self.tax_model = self.env['account.tax']
        self.pis = self.tax_model.create({
            'name': "PIS",
            'amount_type': 'division',
            'domain': 'pis',
            'amount': 0.65,
            'sequence': 1,
            'price_include': True,
        })
        self.cofins = self.tax_model.create({
            'name': "Cofins",
            'amount_type': 'division',
            'domain': 'cofins',
            'amount': 3,
            'sequence': 2,
            'price_include': True,
        })
        self.icms_inter = self.tax_model.create({
            'name': "ICMS Inter",
            'amount_type': 'division',
            'domain': 'icms',
            'amount': 17,
            'sequence': 4,
            'price_include': True,
        })
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # REGRA ICMS (COM E SEM REDUCAO)
        icms_rule = [
            (0, 0,
                {
                    'name': 'ICMS SEM REDUCAO',
                    'tax_id': self.icms_inter.id,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'tipo_produto': 'product',
                    'domain': 'icms'
                }),
            (0, 0,
                {
                    'name': 'ICMS SEM REDUCAO',
                    'tax_id': self.icms_inter.id,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'tipo_produto': 'product',
                    'reducao_icms': 5.00,
                    'product_ids': [(4, self.product_b.id, 0)],
                    'domain': 'icms'
                })]
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # REGRA PIS
        pis_rule = [
            (0, 0,
                {
                    'name': 'PIS',
                    'tax_id': self.pis.id,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'tipo_produto': 'product',
                    'domain': 'pis'
                })]
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # REGRA PIS
        cofins_rule = [
            (0, 0,
                {
                    'name': 'COFINS',
                    'tax_id': self.cofins.id,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'tipo_produto': 'product',
                    'domain': 'cofins'
                })]
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # NFC-E <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        self.nfe_seq = self.env['ir.sequence'].create({
            'name': 'Série 1 - Nota Fiscal Eletrônica',
            'implementation': 'no_gap',
            'padding': 1,
            'number_increment': 1,
            'number_next_actual': 1,
        })
        self.nfe_doc = self.env['br_account.fiscal.document'].create({
            'code': '55',
            'name': 'Nota Fiscal Eletronica',
        })
        self.nfe_serie = self.env['br_account.document.serie'].create({
            'code': '1',
            'active': True,
            'name': 'Série 1 - Nota Fiscal Eletrônica',
            'fiscal_document_id': self.nfe_doc.id,
            'fiscal_type': 'product',
            'internal_sequence_id': self.nfe_seq.id,
            'company_id': self.main_company.id,
        })

        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

        # POSICAO FISCAL
        self.pos_fiscal_position = self.env['account.fiscal.position'].create({
            'name': 'FISCAL POS', 'ind_final': '1', 'ind_pres': '4',
            'nfe_serie': self.nfe_serie.id,
            'icms_tax_rule_ids': icms_rule,
            'pis_tax_rule_ids': pis_rule,
            'cofins_tax_rule_ids': cofins_rule,
        })
        self.pos_config = self.env['pos.config'].create({
            'name': 'POS CONFIG',
            'journal_id': self.journalpos.id,
            'invoice_journal_id': self.journalrec.id,
            'fiscal_position_ids': [(4, self.pos_fiscal_position.id, 0)],
            'default_fiscal_position_id': self.pos_fiscal_position.id,
            'journal_ids': cash_journal,
        })
        self.pos_session = self.env['pos.session'].create({
            'user_id': self.env.user.id,
            'config_id': self.pos_config.id,
            'start_at': datetime.now(),
        })
        self.bank_stt = self.env['account.bank.statement'].create({
            'balance_start': 0.00,
            'journal_id': self.journalpos.id,
            'company_id': self.main_company.id,
            'state': 'open',
            'name': '2016-11-14 18:28:31'
        })

    def test_right_tax(self):
        """
        Vender dois de R$10 produtos com ICMS 17, PIS 0.65, e COFINS 3
        sem reducao, e um de R$5 com ICMS 17, PIS 0.65, e COFINS 3 e
        reducao de 5%, os totais devem ser:
             TOTAL: R$25.00
            COFINS: R$00.75
              ICMS: R$04.21
               PIS: R$00.16
        """
        order_1 = {'to_invoice': False}
        data_1 = {
            'user_id': self.env.user.id,
            'name': u'Order 00002-085-0083',
            'partner_id': False,
            'amount_paid': 25.00,
            'pos_session_id': self.pos_session.id,
            'lines': [
                (0, 0, {'product_id': self.product_a.id, 'qty': 2,
                        'price_unit': 10,
                        'tax_ids': [(4, self.pis.id, 0),
                                    (4, self.cofins.id, 0),
                                    (4, self.icms_inter.id, 0)]}),
                (0, 0, {'product_id': self.product_b.id, 'qty': 1,
                        'price_unit': 5,
                        'tax_ids': [(4, self.pis.id, 0),
                                    (4, self.cofins.id, 0),
                                    (4, self.icms_inter.id, 0)]}),
            ],
            'creation_date': datetime.now(),
            'statement_ids': [[0, 0, {'journal_id': self.journalpos.id,
                                      'amount': 25,
                                      'name': u'2016-11-14 18:28:31',
                                      'account_id': self.receivable_acc.id,
                                      u'statement_id': self.bank_stt.id}]],
            'fiscal_position_id': self.pos_fiscal_position.id,
            'sequence_number': 1,
            'amount_return': 0,
        }
        order_1['data'] = data_1
        order = self.env['pos.order'].create_from_ui([order_1])
        order = self.env['pos.order'].browse(order[0])
        order_edoc = self.env['invoice.eletronic'].search(
            [('numero_controle', '=', order.numero_controle)])
        self.assertEquals(
            order_edoc.valor_icms, 4.21,
            'Valor de ICMS errado\nEsperado: 4.21 Recebeu: %f' % (
                order_edoc.valor_icms))
        self.assertEquals(order_edoc.valor_pis, 0.16)
        self.assertEquals(order_edoc.valor_cofins, 0.75)
