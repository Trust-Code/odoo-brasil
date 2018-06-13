# -*- coding: utf-8 -*-
# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api

#campo novo para decidir modo de pagamento deve ser adicionado ao account.voucher
class PaymentCnabInformation(models.Model):
    _name = 'l10n_br.payment_cnab'

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s" % (rec.mov_finality or '')))
        return result

    mov_finality = fields.Selection([
        ('01 - Current Account Credit', u'Current Account Credit'),
        ('02 - Rent Payment/Condominium', u'Rent Payment/Condominium'),
        ('03 - Dept Security Payment', u'Dept Security Payment'),
        ('04 - Dividend Payment', u'Dividend Payment'),
        ('05 - Tuition Payment', u'Tuition Payment'),
        ('07 - Provider/Fees Payment', u'Provider/Fees Payment'),
        ('08 - Currency Exchange/Fund/Stock Exchange Payment', u'Currency Exchange/Fund/Stock Exchange Payment'),
        ('09 - Transfer of Collection / Payment of Taxes', u'Transfer of Collection / Payment of Taxes'),
        ('11 - DOC/TED to Saving Account', u'DOC/TED to Saving Account'),
        ('12 - DOC/TED to Judicial Deposit', u'DOC/TED to Judicial Deposit'),
        ('13 - DOC/TED to Judicial Deposit', u'Child Support/Alimony'),
        ('14 - Income Tax Rebate', u'Income Tax Rebate'),
        ('99 - Other', u'Other')
        ], string=u'Movimentation Purpose', default='99')

    operation_code = fields.Selection([
        ('018', u'TED CIP'),
        ('810', u'TED STR'),
        ('700', u'DOC'),
        ('000', u'CC')
    ], string=u'Operation Code', default='000')

    #receiver_warning = fields.Selection([('0', 'No Warning'), ('2', 'Warning only for addresser'), ('5' 'Warning only for receiver'), ('6', 'Warning for both, addresser and receiver')], string=u'Warnings', default='6')

    lote_serv =  fields.Integer('Order of Service')

    reg_type = fields.Integer('Register Type') #muda de acordo com o segmento, pra A e B é 3, deve ser implementado depois como readonly


    # def geraDicionario(self):
    #     dictionaryA = {"controle_banco": 33 , "controle_lote": , "controle_registro": 3, "sequencial_registro_lote": A , "servico_segmento": , "tipo_movimento": , "codigo_instrucao_movimento": , "codigo_camara_compensacao": , "favorecido_banco": , "favorecido_agencia": , "favorecido_agencia_dv":,
    #     "favorecido_conta": , "favorecido_conta_dv": , "favorecido_agencia_conta_dv": , "favorecido_nome": , "numero_documento_cliente": , "data_pagamento": , "tipo_moeda": "BRL", "vazio1": , "valor_pagamento": , "numero_documento_banco": , "data_real_pagamento": , "valor_real_pagamento": ,  "mensagem2":,
    #     "finalidade_doc_ted": ,"vazio2": , "favorecido_emissao_aviso": , "ocorrencias_retorno":  }


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    other_payment = fields.Many2one('l10n_br.payment_cnab', string="Other Payment Information")
