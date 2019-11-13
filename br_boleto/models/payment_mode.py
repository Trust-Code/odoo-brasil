# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from ..boleto.document import getBoletoSelection
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

selection = getBoletoSelection()
IMPLEMENTADOS = ('1', '3', '4', '6', '7', '8', '9', '10')


class PaymentMode(models.Model):
    _inherit = "l10n_br.payment.mode"

    boleto = fields.Boolean(string="Boleto?")
    nosso_numero_sequence = fields.Many2one(
        'ir.sequence', string=u'Seq. do Nosso Número')
    late_payment_fee = fields.Float(string=u"Percentual Multa",
                                    digits=dp.get_precision('Account'))
    late_payment_interest = fields.Float(string=u"Juros de Mora",
                                         digits=dp.get_precision('Account'))
    late_payment_interest_type = fields.Selection([
        ('01', u'JUROS DIA'),
        ('02', u'JUROS MENSAL'),
        ('03', u'ISENTO'),
    ], string=u'Código de Juros', default='03')
    instrucoes = fields.Text(string=u'Instruções')
    boleto_carteira = fields.Char('Carteira', size=3)
    boleto_modalidade = fields.Char('Modalidade', size=2)
    boleto_variacao = fields.Char(u'Variação', size=2)
    boleto_cnab_code = fields.Char(u'Código Convênio', size=20)
    boleto_aceite = fields.Selection(
        [('S', 'Sim'), ('N', 'Não')], string='Aceite', default='N')
    boleto_type = fields.Selection(
        selection, string="Banco do Boleto")
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
        ('4', u'Protestar Fim Falimentar - Dias Úteis'),
        ('5', u'Protestar Fim Falimentar - Dias Corridos'),
        ('7', u'Negativar (Dias Corridos)'),
        ('8', u'Não Negativar')
    ], string=u'Códigos de Protesto', default='0')
    boleto_protesto_prazo = fields.Char(u'Prazo protesto', size=2)

    @api.onchange("boleto_type")
    def br_boleto_onchange_boleto_type(self):
        vals = {}

        if (self.boleto_type) and (self.boleto_type not in IMPLEMENTADOS):
            vals['warning'] = {
                'title': _('Ação Bloqueada!'),
                'message': _('Este boleto ainda não foi implementado!')
            }

        if self.boleto_type == u'1':
            if self.journal_id.bank_account_id.bank_id.bic != '001':
                vals['warning'] = {
                    'title': _('Ação Bloqueada!'),
                    'message':
                    _('Este boleto não combina com a conta bancária!')
                }

            self.boleto_carteira = u'17'
            self.boleto_variacao = u'19'

        if self.boleto_type == u'3':
            if self.journal_id.bank_account_id.bank_id.bic != '237':
                vals['warning'] = {
                    'title': _('Ação Bloqueada!'),
                    'message':
                    _('Este boleto não combina com a conta bancária!')
                }
            self.boleto_carteira = u'9'

        if self.boleto_type == u'4':
            if self.journal_id.bank_account_id.bank_id.bic != '104':
                vals['warning'] = {
                    'title': _('Ação Bloqueada!'),
                    'message':
                    _('Este boleto não combina com a conta bancária!')
                }
            self.boleto_carteira = u'1'
            self.boleto_modalidade = '14'

        if self.boleto_type == u'7':
            if self.journal_id.bank_account_id.bank_id.bic != '033':
                vals['warning'] = {
                    'title': _('Ação Bloqueada!'),
                    'message':
                    _('Este boleto não combina com a conta bancária!')
                }
            self.boleto_carteira = u'101'

        if self.boleto_type == u'9':
            if self.journal_id.bank_account_id.bank_id.bic != '756':
                vals['warning'] = {
                    'title': _('Ação Bloqueada!'),
                    'message':
                    _('Este boleto não combina com a conta bancária!')
                }
            self.boleto_carteira = u'1'
            self.boleto_modalidade = u'01'

        if self.boleto_type == u'10':
            if self.journal_id.bank_account_id.bank_id.bic != '0851':
                vals['warning'] = {
                    'title': _('Ação Bloqueada!'),
                    'message':
                    _('Este boleto não combina com a conta bancária!')
                }
            self.boleto_carteira = '01'
            self.boleto_protesto = '3'

        return vals

    @api.onchange("boleto_carteira")
    def br_boleto_onchange_boleto_carteira(self):
        vals = {}

        if self.boleto_type == u'9' and len(self.boleto_carteira) != 1:
            vals['warning'] = {
                'title': _('Ação Bloqueada!'),
                'message': _('A carteira deste banco possui apenas um digito!')
                }

        return vals

    @api.onchange('boleto_protesto', 'boleto_type')
    def _check_boleto_protesto(self):
        if self.boleto_protesto == '0' and self.boleto_type == '3':
            raise UserError(
                _('Código de protesto inválido para banco Bradesco!'))

    @api.constrains('boleto', 'journal_id', 'type', 'boleto_type')
    def _check_payment_mode(self):
        for rec in self:
            if rec.type != 'receivable' or not rec.boleto:
                continue
            if not rec.journal_id:
                raise ValidationError(_('Para boleto o diário é obrigatório'))
            if not rec.journal_id.bank_account_id:
                raise ValidationError(
                    _('Não existe conta bancária cadastrada no \
                      diário escolhido'))
            if not rec.nosso_numero_sequence:
                raise ValidationError(
                    _('Para boleto a Sequência do Nosso Número é obrigatória'))
            total = self.search_count(
                [('nosso_numero_sequence', '=', rec.nosso_numero_sequence.id),
                 ('id', '!=', rec.id)])
            if total > 0:
                raise ValidationError(
                    _('Sequência já usada em outro modo de pagamento'))
            if not rec.boleto_type:
                raise ValidationError(_('Escolha o banco do boleto!'))

    @api.multi
    def write(self, vals):
        res = super(PaymentMode, self).write(vals)
        self._check_boleto_protesto()
        return res
