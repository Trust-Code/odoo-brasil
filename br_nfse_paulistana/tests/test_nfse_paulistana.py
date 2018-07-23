# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
import logging
from mock import patch
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.xml import sanitize_response
except ImportError:
    _logger.debug('Cannot import pytrustnfe')


class TestNFeBrasil(TransactionCase):

    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestNFeBrasil, self).setUp()
        self.main_company = self.env.ref('base.main_company')
        self.main_company.write({
            'name': 'Trustcode',
            'legal_name': 'Trustcode Tecnologia da Informação',
            'cnpj_cpf': '92.743.275/0001-33',
            'inscr_mun': '51212300',
            'zip': '88037-240',
            'street': 'Vinicius de Moraes',
            'number': '42',
            'district': 'Córrego Grande',
            'country_id': self.env.ref('base.br').id,
            'state_id': self.env.ref('base.state_br_sp').id,
            'city_id': self.env.ref('br_base.city_4205407').id,
            'phone': '(48) 9801-6226',
            'nfe_a1_password': '123456',
            'nfe_a1_file': base64.b64encode(
                open(os.path.join(self.caminho, 'teste.pfx'), 'rb').read()),
        })
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
        self.service_type = self.env.ref('br_data_account.service_type_101')
        self.service_type.codigo_servico_paulistana = '07498'
        self.service = self.env['product.product'].create({
            'name': 'Normal Service',
            'default_code': '25',
            'type': 'service',
            'fiscal_type': 'service',
            'service_type_id': self.service_type.id,
            'list_price': 50.0
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
        self.partner_juridica = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='05.075.837/0001-13',
            company_type='company',
            is_company=True,
            inscr_est='433.992.727',
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
            city_id=self.env.ref('br_base.city_4205407').id,
        ))

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        self.fiscal_doc = self.env['br_account.fiscal.document'].create(dict(
            code='001',
            electronic=True
        ))

        self.serie = self.env['br_account.document.serie'].create(dict(
            code='1',
            active=True,
            name='serie teste',
            fiscal_document_id=self.fiscal_doc.id,
            fiscal_type='product',
            company_id=self.main_company.id,
        ))

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda',
            'service_document_id': self.fiscal_doc.id,
            'service_serie_id': self.serie.id
        })

        invoice_line_data = [
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
            'reference_type': "none",
            'service_document_id': self.env.ref(
                'br_data_account.fiscal_document_001').id,
            'service_serie_id': self.fpos.service_serie_id.id,
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'fiscal_position_id': self.fpos.id,
            'invoice_line_ids': invoice_line_data
        }

        self.invoices = self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_fisica.id
        ))
        self.invoices |= self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_juridica.id
        ))

    def test_computed_fields(self):
        for invoice in self.invoices:
            self.assertEquals(invoice.total_edocs, 0)
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()
            # Verifica algumas propriedades computadas que dependem do edoc
            self.assertEquals(invoice.total_edocs, 1)

    def test_check_invoice_eletronic_values(self):
        for invoice in self.invoices:
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            inv_eletr = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', invoice.id)])

            # TODO Validar os itens que foi setado no invoice e verficar com o
            # documento eletronico
            self.assertEquals(inv_eletr.partner_id, invoice.partner_id)

    @patch('odoo.addons.br_nfse_paulistana.models.invoice_eletronic.teste_envio_lote_rps')  # noqa
    def test_nfse_sucesso_homologacao(self, envio_lote):
        for invoice in self.invoices:
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            # Lote recebido com sucesso
            xml_recebido = open(os.path.join(
                self.caminho, 'xml/nfse-sucesso.xml'), 'r').read()
            resp = sanitize_response(xml_recebido)
            envio_lote.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }
            invoice_eletronic = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', invoice.id)])
            invoice_eletronic.action_send_eletronic_invoice()
            self.assertEqual(invoice_eletronic.state, 'done')
            self.assertEqual(invoice_eletronic.codigo_retorno, '100')
            self.assertEqual(len(invoice_eletronic.eletronic_event_ids), 1)

    @patch('odoo.addons.br_nfse_paulistana.models.invoice_eletronic.cancelamento_nfe')  # noqa
    def test_nfse_cancel(self, cancelar):
        for invoice in self.invoices:
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            # Lote recebido com sucesso
            xml_recebido = open(os.path.join(
                self.caminho, 'xml/cancelamento-sucesso.xml'), 'r').read()
            resp = sanitize_response(xml_recebido)
            cancelar.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }

            invoice_eletronic = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', invoice.id)])
            invoice_eletronic.verify_code = '123'
            invoice_eletronic.numero_nfse = '123'
            invoice_eletronic.action_cancel_document(
                justificativa="Cancelamento de teste")

            self.assertEquals(invoice_eletronic.state, 'cancel')
            self.assertEquals(invoice_eletronic.codigo_retorno, "100")
            self.assertEquals(invoice_eletronic.mensagem_retorno,
                              "Nota Fiscal Paulistana Cancelada")

    @patch('odoo.addons.br_nfse_paulistana.models.invoice_eletronic.cancelamento_nfe')  # noqa
    def test_nfse_cancelamento_erro(self, cancelar):
        for invoice in self.invoices:
            invoice.company_id.tipo_ambiente_nfse = 'producao'
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            # Lote recebido com sucesso
            xml_recebido = open(os.path.join(
                self.caminho, 'xml/cancelamento-erro.xml'), 'r').read()
            resp = sanitize_response(xml_recebido)
            cancelar.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }

            invoice_eletronic = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', invoice.id)])
            invoice_eletronic.verify_code = '123'
            invoice_eletronic.numero_nfse = '123'
            invoice_eletronic.ambiente = 'producao'
            invoice_eletronic.action_cancel_document(
                justificativa="Cancelamento de teste")
            self.assertEquals(invoice_eletronic.state, 'draft')
            self.assertEquals(invoice_eletronic.codigo_retorno, "1305")
            self.assertEquals(invoice_eletronic.mensagem_retorno,
                              "Assinatura de cancelamento da NFS-e incorreta.")
