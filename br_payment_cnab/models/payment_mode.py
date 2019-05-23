# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
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
         ('08', 'FGTS com Código de Barras'),
         ('09', 'ICMS')],
        string="Tipo de Operação")

    schedule_days_before = fields.Integer('Antecipar em: (dias)')
    one_time_payment = fields.Boolean('Pagar Mensal?')
    one_time_payment_day = fields.Integer('Dia do mês a pagar', default=10)

    service_type = fields.Selection([
        ('03', 'Bloqueto Eletrônico'),
        ('10', 'Pagamento Dividendos'),
        ('20', 'Pagamento Fornecedor'),
        ('22', 'Pagamento de Contas, Tributos e Impostos'),
        ('30', 'Pagamento de Salários'),
        ('50', 'Pagamento Sinistros Segurados'),
        ('60', 'Pagamento Despesas Viajante em Trânsito'),
        ('70', 'Pagamento Autorizado'),
        ('75', 'Pagamento Credenciados'),
        ('80', 'Pagamento Representantes / Vendedores'),
        ('90', 'Pagamento Benefícios'),
        ('98', 'Pagamento Diversos'),
    ], string="Tipo de Serviço")

    mov_finality = fields.Selection([
        ('01', 'Crédito em Conta Corrente'),
        ('02', 'Pagamento de Aluguel / Condomínio'),
        ('03', 'Pagamento de Duplicatas e Títulos'),
        ('04', 'Pagamento de Dividendos'),
        ('05', 'Pagamento de Mensalidades Escolares'),
        ('06', 'Pagamento de Salários'),
        ('07', 'Pagamento a Fornecedor / Honorários'),
        ('08', 'Pagamento de Câmbio/Fundos/Bolsas'),
        ('09', 'Repasse de Arrecadação / Pagamento de Tributos'),
        ('11', 'DOC/TED para Poupança'),
        ('12', 'DOC/TED para Depósito Judicial'),
        ('13', 'Pensão Alimentícia'),
        ('14', 'Restituição de Imposto de Renda'),
        ('99', 'Outros')
        ], string='Finalidade do Movimento')

    codigo_receita = fields.Char('Código da Receita')

    numero_referencia = fields.Char('Número de Referência')

    identificacao_fgts = fields.Char('Número de Identificação do FGTS')

    cod_recolhimento = fields.Integer('Código de Recolhimento do FGTS')

    conec_social_dv_fgts = fields.Integer("DV do conectividade Social")

    conec_social_fgts = fields.Integer("Lacre do conectividade social")

    percentual_receita_bruta_acumulada = fields.Char(
        string='Percentual de Receita Bruta Acumulada',
        help='Percentual decorrente da receita bruta acumulada a ser aplicado\
        sobre a receita mensal.')

    @api.constrains('type', 'journal_id', 'payment_type')
    def _check_payment_mode_payable(self):
        for rec in self:
            if rec.type != 'payable':
                continue
            if not rec.journal_id:
                raise ValidationError(
                    _('Para pagamentos o diário é obrigatório'))
            if not rec.journal_id.bank_account_id:
                raise ValidationError(
                    _('Não existe conta bancária cadastrada no diário \
                      escolhido'))
            if not rec.journal_id.bank_account_id.l10n_br_convenio_pagamento:
                raise ValidationError(
                    _('Configure o código de convênio na conta bancária!'))
            if not rec.journal_id.l10n_br_sequence_nosso_numero:
                raise ValidationError(
                    _('Não existe sequência para o Nosso Número no \
                    diário escolhido'))
            if not rec.payment_type:
                raise ValidationError(_('Escolha o tipo de operação!'))
