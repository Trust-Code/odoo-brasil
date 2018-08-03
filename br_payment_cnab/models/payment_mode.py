# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentMode(models.Model):
    _inherit = 'payment.mode'

    payment_type = fields.Selection(
        [('01', 'TED - Transferência Bancária'),
         ('02', 'DOC - Transferência Bancária'),
         ('03', 'Pagamento de Títulos'),
         ('04', 'Tributos com código de barras'),
         ('05', 'GPS - Guia de previdencia Social'),
         ('06', 'DARF Normal'),
         ('07', 'DARF Simples'),
         ('08', 'FGTS')],
        string="Tipo de Operação")

    mov_finality = fields.Selection([
        ('01', u'Current Account Credit'),
        ('02', u'Rent Payment/Condominium'),
        ('03', u'Dept Security Payment'),
        ('04', u'Dividend Payment'),
        ('05', u'Tuition Payment'),
        ('07', u'Provider/Fees Payment'),
        ('08', u'Currency Exchange/Fund/Stock Exchange Payment'),
        ('09', u'Transfer of Collection / Payment of Taxes'),
        ('11', u'DOC/TED to Saving Account'),
        ('12', u'DOC/TED to Judicial Deposit'),
        ('13', u'Child Support/Alimony'),
        ('14', u'Income Tax Rebate'),
        ('99', u'Other')
        ], string=u'Move Finality')

    finality_ted = fields.Selection([
        ('01', u'Pagamento de impostos, tributos e taxas'),
        ('02', u'Pagamento Concessionárias Serviço Público'),
        ('03', u'Pagamento de Dividendos'),
        ('04', u'Pagamento de Salários'),
        ('05', u'Pagamento de Fornecedores'),
        ('06', u'Pagamentos de Honorários'),
        ('07', u'Pagamento de Aluguel/Condomínios'),
        ('08', u'Pagamento de Duplicatas/Títulos'),
        ('09', u'Pagamento de Mensalidades Escolares'),
        ('11', u'Crédito em Conta'),
        ('300', u'Restituição de Imposto de Renda')
        ], string=u'TED Purpose')

    codigo_receita = fields.Char('Código da Receita')
