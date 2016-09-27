# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
import re
import time
import base64
from ..febraban.cnab import Cnab
from datetime import datetime
from odoo.exceptions import UserError


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    cnab_file = fields.Binary('CNAB File', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Cliente")
    file_number = fields.Integer(u'Número sequencial do arquivo', readonly=1)
    data_emissao_cnab = fields.Datetime('Data de Emissão do CNAB')
    cnab_valido = fields.Boolean(u'CNAB Válido', readonly=1)

    @api.multi
    def gerar_cnab(self):
        self.data_emissao_cnab = datetime.now()
        self.file_number = self.env['ir.sequence'].next_by_code('cnab.nsa')
        for order_id in self:

            order = self.env['payment.order'].browse(order_id.id)
            cnab = Cnab.get_cnab(
                order.payment_mode_id.bank_account_id.bank_bic,
                order.payment_mode_id.payment_type_id.code)()
            remessa = cnab.remessa(order)
            suf_arquivo = 'ABX'  # order.get_next_sufixo()

            if order.payment_mode_id.payment_type_id.code == '240':
                self.name = 'CB%s%s.REM' % (
                    time.strftime('%d%m'), str(order.file_number))
            elif order.payment_mode_id.payment_type_id.code == '400':
                self.name = 'CB%s%s.REM' % (
                    time.strftime('%d%m'), str(suf_arquivo))
            elif order.payment_mode_id.payment_type_id.code == '500':
                self.name = 'PG%s%s.REM' % (
                    time.strftime('%d%m'), str(order.file_number))
            self.state = 'done'
            self.cnab_file = base64.b64encode(remessa)

            self.env['ir.attachment'].create({
                'name': self.name,
                'datas': self.cnab_file,
                'datas_fname': self.name,
                'description': 'Arquivo CNAB 240',
                'res_model': 'payment.order',
                'res_id': order_id
            })

    def sicoob_validate_header_arquivo(self, line):
        data_emissao = fields.Datetime.from_string(self.data_emissao_cnab)
        hora_emissao = datetime.strftime(data_emissao, '%H%M%S')
        data_emissao = datetime.strftime(data_emissao, '%d%m%Y')
        erros = []
        if line[:3] != '756':
            erros += ['Código Sicoob']
        if line[3:17] != '00000         ':
            erros += ['Controle Lote ou Controle Registro']
        if line[17] not in ('1', '2'):
            erros += ['Tipo de Inscrição da Empresa']
        if line[18:32] != re.sub('[^0-9]', '',
                                 self.user_id.company_id.cnpj_cpf):
            erros += ['Número de Inscrição da Empresa']
        if line[32:52] != (' ' * 20):
            erros += ['Beneficiário Convênio']
        if line[52:57] != self.payment_mode_id.bank_account_id.\
                bra_number.strip().zfill(5):
            erros += ['Número da Agência']
        if line[57] != self.payment_mode_id.bank_account_id.bra_number_dig:
            erros += ['Digito Verificador da Empresa']
        if line[58:70] != self.payment_mode_id.bank_account_id.acc_number.\
                zfill(12):
            erros += ['Número da Conta']
        if line[70] != self.payment_mode_id.bank_account_id.acc_number_dig:
            erros += ['Digito Verificador da Conta']
        if line[71] != ' ':
            erros += ['Digito Verificador Ag/Conta']
        if line[72:102] != self.user_id.company_id.legal_name.ljust(30):
            erros += ['Nome da Empresa']
        if line[102:132] != 'SICOOB'.ljust(30):
            erros += ['Nome do Banco']
        if line[132:142] != (' ' * 10):
            erros += ['CNAB']
        if line[142] != '1':
            erros += ['Código Remessa / Retorno']
        if line[143:151] != data_emissao:
            erros += ['Data de Emissão']
        if line[151:153] not in hora_emissao:
            erros += ['Hora de Emissão']
        if line[157:163] != str(self.file_number).zfill(6):
            erros += ['Numero Sequencial do Arquivo']
        if line[163:166] != '087':
            erros += ['Layout do Arquivo']
        if line[166:171] != ''.zfill(5):
            erros += ['Densidade']
        if line[171:].replace('\r\n', '') != ''.ljust(69):
            erros += ['Campos Reservados ao Banco']
        if len(erros) > 0:
            return '\n * '.join(erros)
        return 'SUCESSO'

    def sicoob_validate_header_lote(self, line):
        data_emissao = fields.Datetime.from_string(self.data_emissao_cnab)
        data_remessa = datetime.strftime(data_emissao, '%d%m%Y')
        erros = []
        if line[:3] != '756':
            erros += ['Código Sicoob']  # deve ser '756'
        if line[3:7] != '0001':
            erros += ['Lote de Serviço']
        if line[7] != '1':
            erros += ['Tipo de Registro']
        if line[8] != 'R':
            erros += ['Tipo de Operação']
        if line[9:11] != '01':
            erros += ['Tipo de Serviço']
        if line[11:13] != '  ':
            erros += ['CNAB (Brancos)']
        if line[13:16] != '040':
            erros += ['Layout do Lote']
        if line[16] != ' ':
            erros += ['CNAB (Branco)']
        if line[17] not in ('1', '2'):
            erros += ['Tipo de Inscrição da Empresa']
        if line[18:33] != re.sub('[^0-9]', '',
                                 self.user_id.company_id.cnpj_cpf).zfill(15):
            erros += ['Número de Inscrição da Empresa']
        if line[33:53] != (' ' * 20):
            erros += ['Convênio (Brancos)']
        if line[53:58] != self.payment_mode_id.bank_account_id.\
                bra_number.strip().zfill(5):
            erros += ['Número da Agência']
        if line[58] != self.payment_mode_id.bank_account_id.bra_number_dig:
            erros += ['Digito Verificador da Agência']
        if line[59:71] != self.payment_mode_id.bank_account_id.acc_number.\
                zfill(12):
            erros += ['Número da Conta']
        if line[71] != self.payment_mode_id.bank_account_id.acc_number_dig:
            erros += ['Digito Verificador da Conta']
        if line[72] != ' ':
            erros += ['Digito Verificador Ag/Conta (Branco)']
        if line[73:103] != self.user_id.company_id.legal_name.ljust(30):
            erros += ['Nome da Empresa']
        if line[103:143] != (' ' * 40):
            erros += ['Informação 1']
        if line[143:183] != (' ' * 40):
            erros += ['Informação 2']
        if line[183:191] != str(self.id).zfill(8):
            erros += ['Número da Remessa']
        if line[191:199] != data_remessa:
            erros += ['Data de Gravação Remessa']
        if line[199:207] != ''.zfill(8):
            erros += ['Data do Crédito']
        if line[207:].replace('\r\n', '') != ''.ljust(33):
            erros += ['CNAB (Brancos)']
        if len(erros) > 0:
            return '\n * '.join(erros)
        else:
            return 'SUCESSO'

    def sicoob_validate_segmento_p(self, line):
        # parcela = '1' if len(self.line_ids) == 1 else '2'
        # nosso_numero = num_titulo + parcela + modalidade + '1' + '     '
        numero_registro = [str(i).zfill(5) if i == 1 else str(i+3).zfill(5)
                           for i in range(5)]
        erros = []
        if line[:3] != '756':
            erros += ['Código Sicoob']
        if line[3:7] != '0001':
            erros += ['Código do Lote']
        if line[7] != '3':
            erros += ['Tipo de Registro']
        if line[8:13] not in numero_registro:
            erros += ['Número de Registro']
        if line[13] != 'P':
            erros += ['Segmento']
        if line[14] != ' ':
            erros += ['Uso Exclusivo FEBRABAN/CNAB']
        if line[15:17] != '01':
            erros += ['Código de Movimento']
        if line[17:22] != self.payment_mode_id.bank_account_id.\
                bra_number.strip().zfill(5):
            erros += ['Número da Agência']
        if line[22] != self.payment_mode_id.bank_account_id.\
                bra_number_dig:
            erros += ['Digito Verificador da Agência']
        if line[23:35] != self.payment_mode_id.bank_account_id.acc_number.\
                zfill(12):
            erros += ['Número da Conta Bancária']
        if line[35] != self.payment_mode_id.bank_account_id.acc_number_dig:
            erros += ['Digito Verificador da Conta']
        if line[36] != ' ':
            erros += ['Digito Verificador da Ag/Conta']
        # TODO: Nosso Numero
        if line[57] != '1':
            erros += ['Código da Carteira']
        if line[58] != '0':
            erros += ['Forma de Cadastramento do Título no Banco']
        if line[59] != ' ':
            erros += ['Tipo de Documento']
        if line[60] != '2':
            erros += ['Identificação da Emissão do Boleto']
        if line[61] != '2':
            erros += ['Identificação da Distribuição do Boleto']
        if line[62:77] != numero_documento:
            erros += ['Número do Documento de Cobrança']
        if line[77:85] != data_vencimento:
            erros += ['Data de Vencimento do Título']
        if len(erros) > 0:
            return '\n'.join(erros)
        else:
            return 'SUCESSO'

    @api.multi
    def validar_cnab(self):
        if self.payment_mode_id.bank_account_id.bank_id.bic == '756':
            cnab = base64.decodestring(self.cnab_file).split('\r\n')
            cnab = [line for line in cnab if len(line) == 240]
            cnab_header_arquivo = cnab[0]
            cnab_header_lote = cnab[1]
            cnab_header_arquivo_erros = \
                self.sicoob_validate_header_arquivo(cnab_header_arquivo)
            cnab_header_lote_erros = \
                self.sicoob_validate_header_lote(cnab_header_lote)
            segmentos = cnab[2:-2]
            dict_segmentos = dict()
            dict_segmentos['P'] = []
            dict_segmentos['Q'] = []
            dict_segmentos['R'] = []
            for seg in segmentos:
                dict_segmentos[seg[13]] += [seg.replace('\r\n', '')]

            if cnab_header_arquivo_erros != 'SUCESSO':
                raise UserError('Header de Arquivo:' + '\n * ' +
                                cnab_header_arquivo_erros)
            elif cnab_header_lote_erros != 'SUCESSO':
                raise UserError('Header de Lote:' + '\n * ' +
                                cnab_header_lote_erros)
