# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
from mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from pytrustnfe.xml import sanitize_response


class TestNFeBrasil(TransactionCase):

    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestNFeBrasil, self).setUp()
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
            'cest': '17.084.00'
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
        self.partner_juridica = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='05.075.837/0001-13',
            company_type='company',
            is_company=True,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sc').id,
            city_id=self.env.ref('br_base.city_4205407').id,
            inscr_est='433.992.727',
        ))
        self.partner_fisica_inter = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='793.493.171-92',
            company_type='person',
            is_company=False,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_rs').id,
            city_id=self.env.ref('br_base.city_4304606').id,
        ))
        self.partner_juridica_inter = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='08.326.476/0001-29',
            company_type='company',
            is_company=True,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_rs').id,
            city_id=self.env.ref('br_base.city_4300406').id,
        ))
        self.partner_juridica_sp = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='37.484.824/0001-94',
            company_type='company',
            is_company=True,
            country_id=self.env.ref('base.br').id,
            state_id=self.env.ref('base.state_br_sp').id,
            city_id=self.env.ref('br_base.city_3501608').id,
        ))
        self.partner_exterior = self.env['res.partner'].create(dict(
            default_partner.items(),
            cnpj_cpf='12345670',
            company_type='company',
            is_company=True,
            country_id=self.env.ref('base.us').id,
        ))

        self.journalrec = self.env['account.journal'].create({
            'name': 'Faturas',
            'code': 'INV',
            'type': 'sale',
            'default_debit_account_id': self.revenue_account.id,
            'default_credit_account_id': self.revenue_account.id,
        })

        self.fiscal_doc = self.env['br_account.fiscal.document'].create(dict(
            code='55',
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
        self.icms_difal_inter_700 = self.env['account.tax'].create({
            'name': "ICMS Difal Inter",
            'amount_type': 'division',
            'domain': 'icms_inter',
            'amount': 7,
            'price_include': True,
        })
        self.icms_difal_intra_1700 = self.env['account.tax'].create({
            'name': "ICMS Difal Intra",
            'amount_type': 'division',
            'domain': 'icms_intra',
            'amount': 17,
            'price_include': True,
        })

        self.fpos = self.env['account.fiscal.position'].create({
            'name': 'Venda',
            'product_document_id': self.fiscal_doc.id,
            'product_serie_id': self.serie.id
        })

        self.fpos_consumo = self.env['account.fiscal.position'].create({
            'name': 'Venda Consumo',
            'ind_final': '1',
            'product_document_id': self.fiscal_doc.id,
            'product_serie_id': self.serie.id
        })
        invoice_line_incomplete = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'quantity': 10.0,
                    'account_id': self.revenue_account.id,
                    'name': 'product test 5',
                    'price_unit': 100.00,
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
                }
             )
        ]
        invoice_line_data = [
            (0, 0,
                {
                    'product_id': self.default_product.id,
                    'uom_id': self.default_product.uom_id.id,
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
                    'fiscal_classification_id': self.default_ncm.id,
                    'tem_difal': True,
                    'tax_icms_inter_id': self.icms_difal_inter_700.id,
                    'tax_icms_intra_id': self.icms_difal_intra_1700.id,
                }
             ),
            (0, 0,
                {
                    'product_id': self.service.id,
                    'uom_id': self.default_product.uom_id.id,
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
                    'fiscal_classification_id': self.default_ncm.id,
                }
             )
        ]
        default_invoice = {
            'name': "Teste Validação",
            'reference_type': "none",
            'product_document_id': self.env.ref(
                'br_data_account.fiscal_document_55').id,
            'journal_id': self.journalrec.id,
            'account_id': self.receivable_account.id,
            'fiscal_position_id': self.fpos.id,
            'invoice_line_ids': invoice_line_data,
            'product_serie_id': self.serie.id,
            'freight_responsibility': '0',
            'shipping_supplier_id': self.partner_juridica.id,
        }
        self.inv_incomplete = self.env['account.invoice'].create(dict(
            name="Teste Validação",
            reference_type="none",
            product_document_id=self.env.ref(
                'br_data_account.fiscal_document_55').id,
            journal_id=self.journalrec.id,
            partner_id=self.partner_fisica.id,
            account_id=self.receivable_account.id,
            invoice_line_ids=invoice_line_incomplete,
            product_serie_id=self.serie.id,
            fiscal_position_id=self.fpos.id,
        ))

        self.invoices = self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_fisica.id
        ))
        self.invoices |= self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_juridica.id
        ))
        self.invoices |= self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_juridica.id,
            fiscal_position_id=self.fpos_consumo.id
        ))
        self.invoices |= self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_fisica_inter.id
        ))
        self.invoices |= self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_juridica_inter.id
        ))
        self.invoices |= self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_juridica_sp.id
        ))
        self.invoices |= self.env['account.invoice'].create(dict(
            default_invoice.items(),
            partner_id=self.partner_exterior.id
        ))

    def test_computed_fields(self):
        for invoice in self.invoices:
            self.assertEquals(invoice.total_edocs, 0)
            self.assertEquals(invoice.nfe_number, 0)
            self.assertEquals(invoice.nfe_exception_number, 0)
            self.assertEquals(invoice.nfe_exception, False)
            self.assertEquals(invoice.sending_nfe, False)

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            # Verifica algumas propriedades computadas que dependem do edoc
            self.assertEquals(invoice.total_edocs, 1)
            self.assertTrue(invoice.nfe_number != 0)
            self.assertTrue(invoice.nfe_exception_number != 0)
            self.assertEquals(invoice.nfe_exception, False)
            self.assertEquals(invoice.sending_nfe, True)

    def test_print_actions(self):
        for invoice in self.invoices:
            # Antes de confirmar a fatura
            with self.assertRaises(UserError):
                invoice.action_preview_danfe()

            # Testa a impressão normal quando não é documento eletrônico
            invoice.product_document_id.code = '00'
            vals_print = invoice.invoice_print()
            self.assertEquals(vals_print['report_name'],
                              'account.report_invoice_with_payments')
            invoice.product_document_id.code = '55'

            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            danfe = invoice.invoice_print()
            self.assertEquals(danfe['report_name'],
                              'br_nfe.main_template_br_nfe_danfe')

    @patch('odoo.addons.br_nfe.models.invoice_eletronic.InvoiceEletronic._prepare_lote')  # noqa
    def test_check_invoice_eletronic_values(self, prepare):
        def _prepare_lote(lote, nfe_values):
            # Let's fix some values
            nfe_values['ide']['cNF'] = '66382470'
            nfe_values['ide']['dhEmi'] = '2018-05-21T14:19:37-00:00'
            nfe_values['ide']['dhSaiEnt'] = '2018-05-21T14:19:37-00:00'
            nfe_values['cobr']['dup'][0]['dVenc'] = '2018-05-21'
            return {
                'idLote': nfe_values['ide']['nNF'],
                'indSinc': 0,
                'estado': nfe_values['ide']['cUF'],
                'ambiente': 2,
                'NFes': [{
                    'infNFe': nfe_values
                }],
                'modelo': '55',
            }

        prepare.side_effect = _prepare_lote
        for invoice in self.invoices:
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            inv_eletr = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', invoice.id)])

            xml_generated = base64.decodestring(inv_eletr.xml_to_send)

            name = '%s.xml' % invoice.number.replace('/', '-')
            with open(os.path.join(self.caminho, 'xml/%s' % name), 'r') as f:
                xml_test = f.read()
                # f.write(xml_generated.decode('utf-8'))

            self.assertEquals(inv_eletr.partner_id, invoice.partner_id)
            self.assertEquals(xml_test, xml_generated.decode('utf-8'))

    def test_nfe_validation(self):
        with self.assertRaises(UserError):
            self.inv_incomplete.action_invoice_open()

    def test_send_nfe(self):
        for invoice in self.invoices:
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            invoice_eletronic = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', invoice.id)])
            with self.assertRaises(Exception):
                invoice_eletronic.action_send_eletronic_invoice()

    @patch('odoo.addons.br_nfe.models.invoice_eletronic.retorno_autorizar_nfe')
    @patch('odoo.addons.br_nfe.models.invoice_eletronic.autorizar_nfe')
    def test_nfe_with_concept_error(self, autorizar, ret_autorizar):
        for invoice in self.invoices:
            # Confirmando a fatura deve gerar um documento eletrônico
            invoice.action_invoice_open()

            # Lote recebido com sucesso
            xml_recebido = open(os.path.join(
                self.caminho, 'xml/lote-recebido-sucesso.xml'), 'r').read()
            resp = sanitize_response(xml_recebido)
            autorizar.return_value = {
                'object': resp[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }

            # Consultar recibo com erro 694 - Nao informado o DIFAL
            xml_recebido = open(os.path.join(
                self.caminho, 'xml/recibo-erro-694.xml'), 'r').read()
            resp_ret = sanitize_response(xml_recebido)
            ret_autorizar.return_value = {
                'object': resp_ret[1],
                'sent_xml': '<xml />',
                'received_xml': xml_recebido
            }

            invoice_eletronic = self.env['invoice.eletronic'].search(
                [('invoice_id', '=', invoice.id)])

            invoice_eletronic.action_send_eletronic_invoice()
            self.assertEquals(invoice_eletronic.state, 'error')
            self.assertEquals(invoice_eletronic.codigo_retorno, '694')

    @patch('odoo.addons.br_nfe.models.invoice_eletronic.recepcao_evento_cancelamento')  # noqa
    def test_nfe_cancelamento_ok(self, cancelar):
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

            # As 2 linhas seguintes servem apenas para setar o nfe_processada
            # do invoice_eletronic -> famosa gambiarra
            encoded_xml = '<xml />'.encode('utf-8')
            invoice_eletronic.nfe_processada = base64.encodestring(encoded_xml)

            invoice_eletronic.action_cancel_document(
                justificativa="Cancelamento de teste")

            self.assertEquals(invoice_eletronic.state, 'cancel')
            self.assertEquals(invoice_eletronic.codigo_retorno, "135")
            self.assertEquals(invoice_eletronic.mensagem_retorno,
                              "Evento registrado e vinculado a NF-e")
