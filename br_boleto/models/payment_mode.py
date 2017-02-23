# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.br_boleto.boleto.document import getBoletoSelection
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

selection = getBoletoSelection()
IMPLEMENTADOS = (u'1', u'3', u'7', u'9', u'10')


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    boleto = fields.Boolean(string="Boleto?")
    nosso_numero_sequence = fields.Many2one(
        'ir.sequence', string=u'Seq. do Nosso Número')
    late_payment_fee = fields.Float(string=u"Percentual Multa",
                                    digits=dp.get_precision('Account'))
    late_payment_interest = fields.Float(string=u"Juros de Mora ao Mês",
                                         digits=dp.get_precision('Account'))
    instrucoes = fields.Text(string=u'Instruções')
    boleto_carteira = fields.Char('Carteira', size=3)
    boleto_modalidade = fields.Char('Modalidade', size=2)
    boleto_variacao = fields.Char(u'Variação', size=2)
    boleto_cnab_code = fields.Char(u'Código Convênio', size=20)
    boleto_aceite = fields.Selection(
        [('S', 'Sim'), ('N', 'Não')], string='Aceite', default='N')
    boleto_type = fields.Selection(
        selection, string="Boleto")
    boleto_especie = fields.Selection([
        ('01', u'DUPLICATA MERCANTIL'),
        ('02', u'NOTA PROMISSÓRIA'),
        ('03', u'NOTA DE SEGURO'),
        ('04', u'MENSALIDADE ESCOLAR'),
        ('05', u'RECIBO'),
        ('06', u'CONTRATO'),
        ('07', u'COSSEGUROS'),
        ('08', u'DUPLICATA DE SERVIÇO'),
        ('09', u'LETRA DE CÂMBIO'),
        ('13', u'NOTA DE DÉBITOS'),
        ('15', u'DOCUMENTO DE DÍVIDA'),
        ('16', u'ENCARGOS CONDOMINIAIS'),
        ('17', u'CONTA DE PRESTAÇÃO DE SERVIÇOS'),
        ('99', u'DIVERSOS'),
    ], string=u'Espécie do Título', default='01')
    boleto_protesto = fields.Selection([
        ('0', u'Sem instrução'),
        ('1', u'Protestar (Dias Corridos)'),
        ('2', u'Protestar (Dias Úteis)'),
        ('3', u'Não protestar'),
        ('7', u'Negativar (Dias Corridos)'),
        ('8', u'Não Negativar')
    ], string=u'Códigos de Protesto', default='0')
    boleto_protesto_prazo = fields.Char(u'Prazo protesto', size=2)

    @api.onchange("boleto_type")
    def br_boleto_onchange_boleto_type(self):
        vals = {}

        if self.boleto_type not in IMPLEMENTADOS:
            vals['warning'] = {
                'title': u'Ação Bloqueada!',
                'message': u'Este boleto ainda não foi implentado!'
            }

        if self.boleto_type == u'1':
            if self.bank_account_id.bank_id.bic != '001':
                vals['warning'] = {
                    'title': u'Ação Bloqueada!',
                    'message': u'Este boleto não combina com a conta bancária!'
                }

            self.boleto_carteira = u'17'
            self.boleto_variacao = u'19'

        if self.boleto_type == u'3':
            if self.bank_account_id.bank_id.bic != '237':
                vals['warning'] = {
                    'title': u'Ação Bloqueada!',
                    'message': u'Este boleto não combina com a conta bancária!'
                }
            self.boleto_carteira = u'9'

        if self.boleto_type == u'7':
            if self.bank_account_id.bank_id.bic != '033':
                vals['warning'] = {
                    'title': u'Ação Bloqueada!',
                    'message': u'Este boleto não combina com a conta bancária!'
                }
            self.boleto_carteira = u'101'

        if self.boleto_type == u'9':
            if self.bank_account_id.bank_id.bic != '756':
                vals['warning'] = {
                    'title': u'Ação Bloqueada!',
                    'message': u'Este boleto não combina com a conta bancária!'
                }
            self.boleto_carteira = u'1'
            self.boleto_modalidade = u'01'

        if self.boleto_type == u'10':
            if self.bank_account_id.bank_id.bic != '0851':
                vals['warning'] = {
                    'title': u'Ação Bloqueada!',
                    'message': u'Este boleto não combina com a conta bancária!'
                }
            self.boleto_carteira = '01'
            self.boleto_protesto = '3'

        return vals

    @api.onchange("boleto_carteira")
    def br_boleto_onchange_boleto_carteira(self):
        vals = {}

        if self.boleto_type == u'9' and len(self.boleto_carteira) != 1:
            vals['warning'] = {
                'title': u'Ação Bloqueada!',
                'message': 'A carteira deste banco possui apenas um digito!'
                }

        return vals
