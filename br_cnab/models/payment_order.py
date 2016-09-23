# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
import re
import time
import base64
from ..febraban.cnab import Cnab
from datetime import datetime


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    cnab_file = fields.Binary('CNAB File', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Cliente")
    file_number = fields.Integer(u'Número sequencial do arquivo', readonly=1)
    data_emissao_cnab = fields.Datetime('Data de Emissão do CNAB')

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

    def validate_header_arquivo(self, line):
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
                bra_number.zfill(5):
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
        if line[72:102] != self.user_id.company_id.legal_name:
            erros += ['Nome da Empresa']
        if line[102:132] != 'SICOOB'.ljust(30):
            erros += ['Nome do Banco']
        if line[132:142] != (' ' * 10):
            erros += ['CNAB']
        if line[142] != '1':
            erros += ['Código Remessa / Retorno']
        if line[143:151] != data_emissao:
            erros += ['Data de Emissão']
        if line[151:157] != hora_emissao:
            erros += ['Hora de Emissão']
        if line[157:163] != str(self.nsa_cnab).zfill(6):
            erros += ['Numero Sequencial do Arquivo']
        if line[163:166] != '087':
            erros += ['Layout do Arquivo']
        if line[166:171] != ''.zfill(5):
            erros += ['Densidade']
        if line[171:].replace('\r\n', '') != ''.ljust(69):
            erros += ['Campos Reservados ao Banco']
        if len(erros) > 0:
            return '\n'.join(erros)
        return 'SUCESSO'

    @api.multi
    def validar_cnab(self):
        if self.payment_mode_id.bank_account_id.bank_id.bic == '756':
            import ipdb; ipdb.set_trace()
            cnab = self.env['ir.attachment'].browse(self.id)
            self.validate_header_arquivo()
            pass
