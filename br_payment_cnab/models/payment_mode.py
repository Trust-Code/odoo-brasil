# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PaymentMode(models.Model):
    _inherit = 'l10n_br.payment.mode'

    payment_type = fields.Selection(
        [('01', 'TED - Transferência Bancária'),
         ('02', 'DOC - Transferência Bancária'),
         ('03', 'Pagamento de Títulos'),
         ('04', 'Tributos com código de barras'),
         ('05', 'GPS - Guia de previdencia Social'),
         ('06', 'DARF Normal'),
         ('07', 'DARF Simples'),
         ('08', 'FGTS'),
         ('09', 'ICMS')],
        string="Tipo de Operação")

    schedule_days_before = fields.Integer('Antecipar em: (dias)')
    one_time_payment = fields.Boolean('Pagar Mensal?')
    one_time_payment_day = fields.Integer('Dia do mês a pagar', default=10)

    mov_finality = fields.Selection([
        ('01', 'Current Account Credit'),
        ('02', 'Rent Payment/Condominium'),
        ('03', 'Dept Security Payment'),
        ('04', 'Dividend Payment'),
        ('05', 'Tuition Payment'),
        ('07', 'Provider/Fees Payment'),
        ('08', 'Currency Exchange/Fund/Stock Exchange Payment'),
        ('09', 'Transfer of Collection / Payment of Taxes'),
        ('11', 'DOC/TED to Saving Account'),
        ('12', 'DOC/TED to Judicial Deposit'),
        ('13', 'Child Support/Alimony'),
        ('14', 'Income Tax Rebate'),
        ('99', 'Other')
        ], string=u'Move Finality')

    finality_ted = fields.Selection([
        ('01', 'Pagamento de impostos, tributos e taxas'),
        ('02', 'Pagamento Concessionárias Serviço Público'),
        ('03', 'Pagamento de Dividendos'),
        ('04', 'Pagamento de Salários'),
        ('05', 'Pagamento de Fornecedores'),
        ('06', 'Pagamentos de Honorários'),
        ('07', 'Pagamento de Aluguel/Condomínios'),
        ('08', 'Pagamento de Duplicatas/Títulos'),
        ('09', 'Pagamento de Mensalidades Escolares'),
        ('11', 'Crédito em Conta'),
        ('300', 'Restituição de Imposto de Renda')
        ], string=u'TED Purpose')

    codigo_receita = fields.Char('Código da Receita')

    numero_referencia = fields.Char('Número de Referência')

    percentual_receita_bruta_acumulada = fields.Char(
        string='Percentual de Receita Bruta Acumulada',
        help='Percentual decorrente da receita bruta acumulada a ser aplicado\
        sobre a receita mensal.')

    l10n_br_environment = fields.Selection(
        [('test', 'Test'),
         ('production', 'Production')],
        string='Environment',
        default='production'
    )

    @api.constrains('type', 'journal_id', 'payment_type')
    def _check_payment_mode_payable(self):
        for rec in self:
            if rec.type != 'payable':
                continue
            if not rec.journal_id:
                raise ValidationError('Para pagamentos o diário é obrigatório')
            if not rec.journal_id.bank_account_id:
                raise ValidationError(
                    'Não existe conta bancária cadastrada no diário escolhido')
            if not rec.journal_id.l10n_br_sequence_nosso_numero:
                raise ValidationError(
                    'Não existe sequência para o Nosso Número no \
                    diário escolhido')
            if not rec.payment_type:
                raise ValidationError('Escolha o tipo de operação!')
