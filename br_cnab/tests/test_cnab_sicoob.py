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
        mode = self.env['payment.mode'].create({
            'name': 'Sicoob',
            'boleto_type': '9',
            'boleto_carteira': '1',
            'boleto_modalidade': '01',
            'nosso_numero_sequence': sequencia.id,
            'bank_account_id': conta.id
        })
        return mode.id

    # def sicoob_validate_header_arquivo(self, line):
    #     data_emissao = fields.Datetime.from_string(self.data_emissao_cnab)
    #     hora_emissao = datetime.strftime(data_emissao, '%H%M%S')
    #     data_emissao = datetime.strftime(data_emissao, '%d%m%Y')
    #     erros = []
    #     if line[:3] != '756':
    #         erros += ['Código Sicoob']
    #     if line[3:17] != '00000         ':
    #         erros += ['Controle Lote ou Controle Registro']
    #     if line[17] not in ('1', '2'):
    #         erros += ['Tipo de Inscrição da Empresa']
    #     if line[18:32] != re.sub('[^0-9]', '',
    #                              self.user_id.company_id.cnpj_cpf):
    #         erros += ['Número de Inscrição da Empresa']
    #     if line[32:52] != (' ' * 20):
    #         erros += ['Beneficiário Convênio']
    #     if line[52:57] != self.payment_mode_id.bank_account_id.\
    #             bra_number.strip().zfill(5):
    #         erros += ['Número da Agência']
    #     if line[57] != self.payment_mode_id.bank_account_id.bra_number_dig:
    #         erros += ['Digito Verificador da Empresa']
    #     if line[58:70] != self.payment_mode_id.bank_account_id.acc_number.\
    #             zfill(12):
    #         erros += ['Número da Conta']
    #     if line[70] != self.payment_mode_id.bank_account_id.acc_number_dig:
    #         erros += ['Digito Verificador da Conta']
    #     if line[71] != ' ':
    #         erros += ['Digito Verificador Ag/Conta']
    #     if line[72:102] != self.user_id.company_id.legal_name.ljust(30):
    #         erros += ['Nome da Empresa']
    #     if line[102:132] != 'SICOOB'.ljust(30):
    #         erros += ['Nome do Banco']
    #     if line[132:142] != (' ' * 10):
    #         erros += ['CNAB']
    #     if line[142] != '1':
    #         erros += ['Código Remessa / Retorno']
    #     if line[143:151] != data_emissao:
    #         erros += ['Data de Emissão']
    #     if line[151:153] not in hora_emissao:
    #         erros += ['Hora de Emissão']
    #     if line[157:163] != str(self.file_number).zfill(6):
    #         erros += ['Numero Sequencial do Arquivo']
    #     if line[163:166] != '087':
    #         erros += ['Layout do Arquivo']
    #     if line[166:171] != ''.zfill(5):
    #         erros += ['Densidade']
    #     if line[171:].replace('\r\n', '') != ''.ljust(69):
    #         erros += ['Campos Reservados ao Banco']
    #     if len(erros) > 0:
    #         return '\n * '.join(erros)
    #     return 'SUCESSO'
    #
    # def sicoob_validate_header_lote(self, line):
    #     data_emissao = fields.Datetime.from_string(self.data_emissao_cnab)
    #     data_remessa = datetime.strftime(data_emissao, '%d%m%Y')
    #     erros = []
    #     if line[:3] != '756':
    #         erros += ['Código Sicoob']  # deve ser '756'
    #     if line[3:7] != '0001':
    #         erros += ['Lote de Serviço']
    #     if line[7] != '1':
    #         erros += ['Tipo de Registro']
    #     if line[8] != 'R':
    #         erros += ['Tipo de Operação']
    #     if line[9:11] != '01':
    #         erros += ['Tipo de Serviço']
    #     if line[11:13] != '  ':
    #         erros += ['CNAB (Brancos)']
    #     if line[13:16] != '040':
    #         erros += ['Layout do Lote']
    #     if line[16] != ' ':
    #         erros += ['CNAB (Branco)']
    #     if line[17] not in ('1', '2'):
    #         erros += ['Tipo de Inscrição da Empresa']
    #     if line[18:33] != re.sub('[^0-9]', '',
    #                              self.user_id.company_id.cnpj_cpf).zfill(15):
    #         erros += ['Número de Inscrição da Empresa']
    #     if line[33:53] != (' ' * 20):
    #         erros += ['Convênio (Brancos)']
    #     if line[53:58] != self.payment_mode_id.bank_account_id.\
    #             bra_number.strip().zfill(5):
    #         erros += ['Número da Agência']
    #     if line[58] != self.payment_mode_id.bank_account_id.bra_number_dig:
    #         erros += ['Digito Verificador da Agência']
    #     if line[59:71] != self.payment_mode_id.bank_account_id.acc_number.\
    #             zfill(12):
    #         erros += ['Número da Conta']
    #     if line[71] != self.payment_mode_id.bank_account_id.acc_number_dig:
    #         erros += ['Digito Verificador da Conta']
    #     if line[72] != ' ':
    #         erros += ['Digito Verificador Ag/Conta (Branco)']
    #     if line[73:103] != self.user_id.company_id.legal_name.ljust(30):
    #         erros += ['Nome da Empresa']
    #     if line[103:143] != (' ' * 40):
    #         erros += ['Informação 1']
    #     if line[143:183] != (' ' * 40):
    #         erros += ['Informação 2']
    #     if line[183:191] != str(self.id).zfill(8):
    #         erros += ['Número da Remessa']
    #     if line[191:199] != data_remessa:
    #         erros += ['Data de Gravação Remessa']
    #     if line[199:207] != ''.zfill(8):
    #         erros += ['Data do Crédito']
    #     if line[207:].replace('\r\n', '') != ''.ljust(33):
    #         erros += ['CNAB (Brancos)']
    #     if len(erros) > 0:
    #         return '\n * '.join(erros)
    #     else:
    #         return 'SUCESSO'

    def test_gen_account_move_line(self):
        self.invoices.action_invoice_open()
        move = self.invoices.receivable_move_line_ids[0]
        move.action_register_boleto()

        ordem_cobranca = self.env['payment.order'].search([
            ('state', '=', 'draft')
        ], limit=1)
        ordem_cobranca.gerar_cnab()
        cnab = base64.decodestring(ordem_cobranca.cnab_file).split('\r\n')
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
