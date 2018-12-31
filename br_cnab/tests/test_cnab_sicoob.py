# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo.addons.br_cnab.tests.test_cnab_common import TestCnab


class TestCnabSicoob(TestCnab):

    def _return_payment_mode(self):
        super(TestCnabSicoob, self)._return_payment_mode()
        sequencia = self.env['ir.sequence'].create({
            'name': "Nosso Numero"
        })
        sicoob = self.env['res.bank'].search([('bic', '=', '756')])
        conta = self.env['res.partner.bank'].create({
            'acc_number': '12345',  # 5 digitos
            'acc_number_dig': '0',  # 1 digito
            'bra_number': '1234',  # 4 digitos
            'bra_number_dig': '0',
            'codigo_convenio': '123456-7',  # 7 digitos
            'bank_id': sicoob.id,
        })
        journal = self.env['account.journal'].create({
            'name': 'Banco Sicoob',
            'code': 'SIC',
            'type': 'bank',
            'bank_account_id': conta.id,
            'company_id': self.main_company.id,
        })
        mode = self.env['l10n_br.payment.mode'].create({
            'name': 'Sicoob',
            'boleto': True,
            'boleto_type': '9',
            'boleto_carteira': '1',
            'boleto_modalidade': '01',
            'nosso_numero_sequence': sequencia.id,
            'journal_id': journal.id,
        })
        return mode.id

    def test_gen_account_move_line(self):
        self.invoices.action_invoice_open()

        self.env['payment.order.line'].action_register_boleto(
            self.invoices.receivable_move_line_ids)

        ordem_cobranca = self.env['payment.order'].search([
            ('state', '=', 'draft')
        ], limit=1)
        ordem_cobranca.gerar_cnab()
        cnab = base64.decodestring(ordem_cobranca.cnab_file)
        cnab = cnab.decode('utf-8').split('\r\n')
        cnab.pop()

        self.assertEquals(len(cnab), 7)  # 8 linhas

        for line in cnab:
            self.assertEquals(len(line), 240)  # 8 linhas

        # TODO Descomentar e implementar teste

        # cnab_header_arquivo = cnab[0]
        # cnab_header_lote = cnab[1]
        # cnab_header_arquivo_erros = \
        #     self.sicoob_validate_header_arquivo(cnab_header_arquivo)
        # cnab_header_lote_erros = \
        #     self.sicoob_validate_header_lote(cnab_header_lote)
        # segmentos = cnab[2:-2]
        # dict_segmentos = dict()
        # dict_segmentos['P'] = []
        # dict_segmentos['Q'] = []
        # dict_segmentos['R'] = []
        # for seg in segmentos:
        #     dict_segmentos[seg[13]] += [seg.replace('\r\n', '')]
        #
        # if cnab_header_arquivo_erros != 'SUCESSO':
        #     raise UserError('Header de Arquivo:' + '\n * ' +
        #                     cnab_header_arquivo_erros)
        # elif cnab_header_lote_erros != 'SUCESSO':
        #     raise UserError('Header de Lote:' + '\n * ' +
        #                     cnab_header_lote_erros)
