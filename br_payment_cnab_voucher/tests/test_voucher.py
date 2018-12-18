# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import base64
from datetime import date
from odoo.exceptions import UserError
from odoo.addons.br_payment_cnab.tests.test_cnab import TestBaseCnab


class TestVoucher(TestBaseCnab):

    caminho = os.path.dirname(__file__)

    def setUp(self):
        super(TestVoucher, self).setUp()
        self.voucher_vals = {
            'voucher_type': 'purchase',
            'journal_id': self.journal_payment.id,
            'account_date': '2018-11-27',
            'date': '2018-11-27',
            'date_due': '2018-11-30',
            'line_ids': [(0, 0, {
                'name': 'Salario',
                'account_id': self.expense_account.id,
                'quantity': 1,
                'price_unit': 125.56
            })]
        }

    def test_copy_voucher(self):
        voucher = self.env['account.voucher'].create(dict(
            self.voucher_vals.items(),
            partner_id=self.partner_fisica.id,
            account_id=self.partner_fisica.property_account_payable_id.id,
            linha_digitavel='85810000014-5 24680270200-8 32415823300-6 01852018107-0'  # noqa
        ))
        self.assertEqual(
            voucher.linha_digitavel,
            '85810000014-5 24680270200-8 32415823300-6 01852018107-0'
        )
        copy = voucher.copy()
        self.assertEqual(copy.linha_digitavel, False)
        self.assertEqual(copy.barcode, False)

    def test_barcode_linha_digitavel(self):
        voucher = self.env['account.voucher'].create(dict(
            self.voucher_vals.items(),
            partner_id=self.partner_fisica.id,
            account_id=self.partner_fisica.property_account_payable_id.id,
            # Tributos
            linha_digitavel='85810000014-5 24680270200-8 32415823300-6 01852018107-0'  # noqa
        ))
        voucher._onchange_linha_digitavel()
        self.assertEqual(
            voucher.barcode,
            '85810000014246802702003241582330001852018107'
        )
        self.assertEqual(voucher.amount, 1424.68)
        # Titulo normal
        voucher.linha_digitavel = \
            '75691.30698 01245.640006 00373.360015 5 76560000033435'
        voucher._onchange_linha_digitavel()
        self.assertEqual(
            voucher.barcode,
            '75695765600000334351306901245640000037336001'
        )
        self.assertEqual(voucher.date_due, '2018-09-23')
        self.assertEqual(voucher.amount, 334.35)

        with self.assertRaises(UserError):
            # Linha digitavel de tamanho invalido
            voucher.linha_digitavel = '123456'

        with self.assertRaises(UserError):
            # Linha digitavel de digito invalido - modificado ultimo digito
            voucher.linha_digitavel = \
                '75691.30698 01245.640006 00373.360015 5 76560000033436'

        # Remove a linha e testa se o onchange cria uma linha
        self.voucher_vals.pop('line_ids')
        voucher = self.env['account.voucher'].new(dict(
            self.voucher_vals.items(),
            partner_id=self.partner_fisica.id,
            account_id=self.partner_fisica.property_account_payable_id.id,
            # Tributos
            linha_digitavel='85810000014-5 24680270200-8 32415823300-6 01852018107-0'   # noqa
        ))
        voucher._onchange_linha_digitavel()
        self.assertEqual(len(voucher.line_ids), 1)
        self.assertEqual(voucher.amount, 1424.68)

    def test_voucher_onchanges(self):
        voucher = self.env['account.voucher'].new(dict(
            self.voucher_vals.items(),
            partner_id=self.partner_fisica.id,
            account_id=self.partner_fisica.property_account_payable_id.id,
            payment_mode_id=self.ted_payment[0].id,
        ))
        voucher._onchange_payment_mode_id()
        voucher._onchange_payment_cnab_partner_id()
        self.assertEqual(voucher.payment_type, '01')   # TED
        self.assertNotEqual(voucher.bank_account_id.id, False)

    def test_voucher_cancel(self):
        voucher = self.env['account.voucher'].create(dict(
            self.voucher_vals.items(),
            partner_id=self.partner_fisica.id,
            account_id=self.partner_fisica.property_account_payable_id.id,
            payment_mode_id=self.titulos_payment[0].id,
            linha_digitavel='75691.30698 01245.640006 00373.360015 5 76560000033435'  # noqa
        ))
        voucher._onchange_linha_digitavel()
        voucher.proforma_voucher()
        lines = self.env['payment.order.line'].search([])
        self.assertEqual(len(lines), 1)
        # Cancelar
        voucher.journal_id.update_posted = True
        voucher.cancel_voucher()
        lines = self.env['payment.order.line'].search([])
        self.assertEqual(len(lines), 0)

        voucher.proforma_voucher()
        lines = self.env['payment.order.line'].search([])
        lines.action_aprove_payment_line()
        with self.assertRaises(UserError):
            voucher.cancel_voucher()

    # TODO Criar teste para campos de juros e multas
    def test_voucher_ted(self):
        vouchers = self.env['account.voucher']
        doc_ted_payments = self.ted_payment | self.doc_payment
        for mode in doc_ted_payments:
            for conta in self.dest_bank_accounts:
                voucher = self.env['account.voucher'].create(dict(
                    self.voucher_vals.items(),
                    partner_id=conta.partner_id.id,
                    bank_account_id=conta.id,
                    account_id=conta.partner_id.property_account_payable_id.id,
                    payment_mode_id=mode.id,
                ))
                voucher.proforma_voucher()
                vouchers |= voucher

        lines = self.env['payment.order.line'].search([])
        # 2 parceiros x 4 bancos x 4 bancos dest x 2 operacoes (ted, doc) = 64
        self.assertEqual(len(lines),  64)

        # Aprova todas as linhas
        lines.action_aprove_payment_line()

        orders = self.env['payment.order'].search([])
        # Uma ordem por banco de origem = 4
        self.assertEqual(len(orders), 4)

        for order in orders:
            self.assertEqual(order.cnab_file, None)
            order.action_generate_payable_cnab()
            self.assertNotEqual(order.cnab_file, None)

            cnab = base64.decodestring(order.cnab_file)
            name = '%s.rem' % order.journal_id.name
            with open(os.path.join(self.caminho, 'cnab/%s' % name), 'w') as f:
                # cnab_teste = f.read()
                # self.assertEqual(cnab_teste, cnab.decode('ascii'))
                f.write(cnab.decode('ascii'))

    def test_boletos_titulos(self):
        boletos = {
            '756': {
                'valor': '1424.68',
                'linha': '85810000014-524680270200-832415823300-601852018107-0'
            },
            '033': {
                'valor': '480.00',
                'linha': '858700000049 800001791819 107622050820 415823300017',
            },
            '237': {
                'valor': '2546.05',
                'linha': '858000000259 460503281831 240720183202 339122710600'
            },
            '341': {
                'valor': '836.73',
                'linha': '858700000081 367301791813 018620053820 415823300017'
            }
        }

        vouchers = self.env['account.voucher']
        for mode in self.tributo_payment:
            voucher = self.env['account.voucher'].create(dict(
                self.voucher_vals.items(),
                partner_id=self.partner_juridica.id,
                account_id=self.partner_juridica.
                property_account_payable_id.id,
                payment_mode_id=mode.id,
                linha_digitavel=boletos[mode.journal_id.code]['linha'],
            ))
            voucher._onchange_linha_digitavel()
            voucher.proforma_voucher()
            vouchers |= voucher

        lines = self.env['payment.order.line'].search([])
        # 4 bancos x 1 boleto
        self.assertEqual(len(lines),  4)

        # Aprova todas as linhas
        lines.action_aprove_payment_line()

        orders = self.env['payment.order'].search([])
        # Uma ordem por banco de origem = 4
        self.assertEqual(len(orders), 4)

        for order in orders:
            self.assertEqual(order.cnab_file, None)
            order.action_generate_payable_cnab()
            self.assertNotEqual(order.cnab_file, None)

        # Testa se estão processados
        statement_id = self.env['l10n_br.payment.statement'].sudo().create({
            'journal_id': lines[0].journal_id.id,
            'date': date.today(),
            'company_id': lines[0].journal_id.company_id.id,
            'name':
            lines[0].journal_id.l10n_br_sequence_statements.next_by_id(),
            'type': 'payable',
        })
        for line in lines:
            statement_id = line.mark_order_line_processed(
                'BD', 'Recebido', statement_id=statement_id)
            self.assertEqual(line.state, 'processed')

        lines.mark_order_line_paid('00', 'Liquidação', statement_id)

        for voucher in vouchers:
            self.assertEqual(
                voucher.l10n_br_residual, 0.0, 'Voucher deve estar pago')

        for line in lines:
            self.assertEqual(line.state, 'paid')
            line.mark_order_line_processed('BD', 'Recebido', statement_id)
            self.assertEqual(line.state, 'paid')
            with self.assertRaises(UserError):
                line.action_aprove_payment_line()
            self.assertEqual(line.state, 'paid')


def test_fgts(self):
        boletos = {
            '756': {
                'valor': '1424.68',
                'linha': '85810000014-524680270200-832415823300-601852018107-0'
            },
            '033': {
                'valor': '480.00',
                'linha': '858700000049 800001791819 107622050820 415823300017',
            },
            '237': {
                'valor': '2546.06',
                'linha': '858000000259 460503281831 240720183202 339122710600'
            },
            '341': {
                'valor': '836.73',
                'linha': '858700000081 367301791813 018620053820 415823300017'
            }
        }

        vouchers = self.env['account.voucher']
        for mode in self.fgts_payment:
            voucher = self.env['account.voucher'].create(dict(
                self.voucher_vals.items(),
                partner_id=self.partner_juridica.id,
                account_id=self.partner_juridica.
                property_account_payable_id.id,
                payment_mode_id=mode.id,
                linha_digitavel=boletos[mode.journal_id.code]['linha'],
            ))
            voucher._onchange_linha_digitavel()
            voucher.proforma_voucher()
            vouchers |= voucher

        lines = self.env['payment.order.line'].search([])
        # 4 bancos x 1 boleto
        self.assertEqual(len(lines),  4)

        # Aprova todas as linhas
        lines.action_aprove_payment_line()

        orders = self.env['payment.order'].search([])
        # Uma ordem por banco de origem = 4
        self.assertEqual(len(orders), 4)

        for order in orders:
            self.assertEqual(order.cnab_file, None)
            order.action_generate_payable_cnab()
            self.assertNotEqual(order.cnab_file, None)

        # Testa se estão processados
        statement_id = self.env['l10n_br.payment.statement'].sudo().create({
            'journal_id': lines[0].journal_id.id,
            'date': date.today(),
            'company_id': lines[0].journal_id.company_id.id,
            'name':
            lines[0].journal_id.l10n_br_sequence_statements.next_by_id(),
            'type': 'payable',
        })
        for line in lines:
            statement_id = line.mark_order_line_processed(
                'BD', 'Recebido', statement_id=statement_id)
            self.assertEqual(line.state, 'processed')

        lines.mark_order_line_paid('00', 'Liquidação')

        for voucher in vouchers:
            self.assertEqual(
                voucher.l10n_br_residual, 0.0, 'Voucher deve estar pago')

        for line in lines:
            self.assertEqual(line.state, 'paid')
            line.mark_order_line_processed('BD', 'Recebido', statement_id)
            self.assertEqual(line.state, 'paid')
            with self.assertRaises(UserError):
                line.action_aprove_payment_line()
            self.assertEqual(line.state, 'paid')
