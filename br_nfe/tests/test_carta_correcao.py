# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import os

from mock import patch
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase
from pytrustnfe.xml import sanitize_response


class TestCartaCorrecao(TransactionCase):

    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestCartaCorrecao, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.main_company.write({
            'name': 'Trustcode',
            'legal_name': 'Trustcode Tecnologia da Informação',
            'cnpj_cpf': '92.743.275/0001-33',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sc').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
            'nfe_a1_password': '123456',
            'nfe_a1_file': base64.b64encode(
                open(os.path.join(self.caminho, 'teste.pfx'), 'rb').read()),
        })
        self.main_company.write({'inscr_est': '219.882.606'})
        self.revenue_account = self.env['account.account'].create({
            'code': '3.0.0',
            'name': 'Receita de Vendas',
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id,
            'company_id': self.main_company.id
        })
        self.receivable_account = self.env['account.account'].create({
            'code': '1.0.0',
            'name': 'Conta de Recebiveis',
            'reconcile': True,
            'user_type_id': self.env.ref(
                'account.data_account_type_receivable').id,
            'company_id': self.main_company.id
        })

        self.default_ncm = self.env['product.fiscal.classification'].create({
            'code': '0201.20.20',
            'name': 'Furniture',
            'federal_nacional': 10.0,
            'estadual_imposto': 10.0,
            'municipal_imposto': 10.0,
            'cest': '123'
        })
        self.default_product = self.env['product.product'].create({
            'name': 'Normal Product',
            'default_code': '12',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 15.0
        })
        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'default_code': '25',
            'type': 'service',
            'fiscal_type': 'service',
            'service_type_id': self.env.ref(
                'br_data_account.service_type_101').id,
            'list_price': 50.0
        })
        self.st_product = self.env['product.product'].create({
            'name': 'Product for ICMS ST',
            'default_code': '15',
            'fiscal_classification_id': self.default_ncm.id,
            'list_price': 25.0
        })
        default_partner = {
            'name': 'Nome Parceiro',
            'legal_name': 'Razão Social',
            'zip': '88037-240',
            'street': 'Endereço Rua',
            'number': '42',
            'district': 'Centro',
            'phone': '(48) 9801-6226',
            'property_account_receivable_id': self.receivable_account.id,
        }
        self.partner_fisica = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='545.770.154-98',
            company_type='person',
            is_company=False,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
            city_id=self.env.ref('br_base.city_4205407').id
        ))
        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda'
        })
        self.fpos_consumo = self.env['account.fiscal.position'].create({
            'name': 'Venda Consumo',
            'ind_final': '1'
        })
        invoice_line_data = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'quantity': 10.0,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'icms_cst_normal': '40',
                    'icms_csosn_simples': '102',
                    'ipi_cst': '50',
                    'pis_cst': '01',
                    'cofins_cst': '01',
                }
             ),
            (0, 0,
                {
                    'product_id': self.service.id,
                    'quantity': 10.0,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
                    'product_type': self.service.fiscal_type,
                    'service_type_id': self.service.service_type_id.id,
                    'cfop_id': self.env.ref(
                        'br_data_account_product.cfop_5101').id,
                    'pis_cst': '01',
                    'cofins_cst': '01',
                }
             )
        ]
        default_invoice = {
            'name': "Teste Validação",
            'product_document_id': self.env.ref(
                'br_data_account.fiscal_document_55').id,
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'fiscal_position_id': self.fpos.id,
            'invoice_line_ids': invoice_line_data,
            'partner_id': self.partner_fisica.id,
        }
        self.account_invoice = self.env['account.invoice'].create(
            default_invoice)
        invoice_eletronic = {
            'model': '55',
            'invoice_id': self.account_invoice.id,
            'partner_id': self.partner_fisica.id,
            'tipo_operacao': 'saida',
            'fiscal_position_id': self.fpos_consumo.id,
            'code': '1',
            'name': 'Teste Carta Correção',
            'company_id': self.main_company.id,
            'chave_nfe': '35161221332917000163550010000000041158176721',
        }
        self.eletronic_doc = self.env['invoice.eletronic'].create(
            invoice_eletronic)
        carta_wizard_short = {
            'correcao': 'short',
            'eletronic_doc_id': self.eletronic_doc.id,
        }
        carta_wizard_long = {
            'correcao': 'long' * 1000,
            'eletronic_doc_id': self.eletronic_doc.id,
        }
        carta_wizard_right = {
            'correcao': 'Teste de Carta de Correcao' * 10,
            'eletronic_doc_id': self.eletronic_doc.id,
        }
        self.carta_wizard_short = self.\
            env['wizard.carta.correcao.eletronica']. create(carta_wizard_short)
        self.carta_wizard_long = self.\
            env['wizard.carta.correcao.eletronica']. create(carta_wizard_long)
        self.carta_wizard_right = self.\
            env['wizard.carta.correcao.eletronica']. create(carta_wizard_right)

    def test_valida_carta_correcao_eletronica(self):
        # Testa validação de carta muito curta (< 15 char)
        with self.assertRaises(UserError):
            self.carta_wizard_short.send_letter()
        # Testa validação de carta muito longa (> 1000 chars)
        with self.assertRaises(UserError):
            self.carta_wizard_long.send_letter()

    @patch('odoo.addons.br_nfe.wizard.carta_correcao_eletronica.recepcao_evento_carta_correcao')  # noqa
    def test_carta_correca_eletronica(self, recepcao):
        # Mock o retorno da CCE
        xml_recebido = open(os.path.join(
            self.caminho, 'xml/cce-retorno.xml'), 'r').read()
        resp = sanitize_response(xml_recebido)
        recepcao.return_value = {
            'object': resp[1],
            'sent_xml': '<xml />',
            'received_xml': xml_recebido
        }
        self.carta_wizard_right.send_letter()

        Id = "ID1101103516122133291700016355001000000004115817672101"
        carta = self.env['carta.correcao.eletronica.evento'].search([])
        self.assertEquals(len(carta), 1)
        self.assertEquals(
            carta.message, u"Evento registrado e vinculado a NF-e")
        self.assertEquals(carta.protocolo, "135160008802236")
        self.assertEquals(carta.correcao, 'Teste de Carta de Correcao' * 10)
        self.assertEquals(carta.sequencial_evento, 1)
        self.assertEquals(carta.tipo_evento, '110110')
        self.assertEquals(carta.id_cce, Id)
