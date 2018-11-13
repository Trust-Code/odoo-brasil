# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


TAX_IDENTIFICATION = {
    '05': '17',
    '06': '16',
    '07': '18',
    '09': '22'
}


class PaymentInformation(models.Model):
    _name = 'l10n_br.payment_information'

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s" % (dict(rec._fields[
                'payment_type'].selection).get(rec.payment_type) or '')))
        return result

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

    operation_code = fields.Selection([     # G14
        ('018', u'TED CIP'),
        ('810', u'TED STR'),
        ('700', u'DOC'),
        ('000', u'CC')
    ], string=u'Operation Code')

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

    warning_code = fields.Selection([
        ('0', u'No Warning'),
        ('2', u'Warning only for addresser'),
        ('5', u'Warning only for receiver'),
        ('6', u'Warning for both, addresser and receiver')
    ], string='Warning Code', default='0')

    mode_payment_indication = fields.Selection([  # sicoob only
        ('01', 'Current Account Debit'),
        ('03', 'Credit Card Debit')
    ], string='Payment Indication', default='03')

    lote_serv = fields.Integer('Order of Service')

    reg_type = fields.Integer('Register Type')

    interest_value = fields.Float('Interest Value')

    fine_value = fields.Float('Duty Value')

    rebate_value = fields.Float('Rebate Value')

    discount_value = fields.Float('Discount Value')

    mov_type = fields.Selection(
        [('0', 'Inclusion'),
         ('5', 'Modification'),
         ('9', 'Exclusion')],
        string='Movimentation Type', default='0')

    mov_instruc = fields.Selection(
        [('00', 'Inclusion of Released Detail Register'),
         ('09', 'Inclusion of Blocked Detail Register(Pending Authorization)'),
         ('10', 'Payment Modification - Released to Blocked'),
         ('11', 'Payment Modification - Blocked to Released'),
         ('14', 'Payment Authorization'),
         ('33', 'Refund Chargeback')],
        string='Movimentation Instrution', default='00')

    service_type = fields.Selection([
        ('03', 'Bloqueto Eletrônico'),
        ('10', 'Pagamento Dividendos'),
        ('20', 'Pagamento Fornecedor'),
        ('22', 'Pagamento de Contas, Tributos e Impostos'),
        ('50', 'Pagamento Sinistros Segurados'),
        ('60', 'Pagamento Despesas Viajante em Trânsito'),
        ('70', 'Pagamento Autorizado'),
        ('75', 'Pagamento Credenciados'),
        ('80', 'Pagamento Representantes / Vendedores'),
        ('90', 'Pagamento Benefícios'),
        ('98', 'Pagamento Diversos'),
    ], string="Tipo de Serviço")

    message2 = fields.Char(string='Note Detail', size=40, default='')

    agency_name = fields.Char(string='Agency Name', size=30, default='')

    currency_code = fields.Selection(
        [('02', 'US Commercial Dolar'),
         ('03', 'US tourism Dolar'),
         ('04', 'ITRD'),
         ('05', 'IDTR'),
         ('06', 'Daily UFIR'),
         ('07', 'Monthly UFIR'),
         ('08', 'FAJ-TR'),
         ('09', 'Real')],
        string="Currency code", default='09')

    message1 = fields.Char(string='Note Header', size=40, default='')

    credit_hist_code = fields.Selection(
        [('0013', 'Dividends Credit'),
         ('0091', 'Casualty Payment - insurance'),
         ('0109', 'Expenses Payment - Travaler in transit'),
         ('0137', 'Agent/Salesman Payment'),
         ('0149', 'INSS Payment'),
         ('0183', 'Provider Payment'),
         ('0197', 'Entry Return'),
         ('0295', 'Accredited Payment'),
         ('2060', 'Same Ownership Transference'),
         ('0367', 'Alimony Payment'),
         ('0491', 'Foresight Rescue'),
         ('0493', 'Foresight Payment'),
         ('0495', 'Foresight Chargeback'),
         ('1070', 'Balance Transference'),
         ('2214', 'Several Credits'),
         ('8051', 'Provider Payment - Receipt'),
         ('2039', 'Several Payments - Provider'),
         ('2644', 'Benefit')],
        string='History Code')

    codigo_receita = fields.Char('Código da Receita')

    tax_identification = fields.Selection(
        [('16', 'DARF Normal'),
         ('18', 'DARF Simples'),
         ('17', 'GPS (Guia da Previdência Social)'),
         ('22', 'GARE-SP ICMS'),
         ('23', 'GARE-SP DR'),
         ('24', 'GARE-SP ITCMD')],
        string="Tax Identification",
        compute='_compute_tax_identification')

    numero_referencia = fields.Char('Número de Referência')

    percentual_receita_bruta_acumulada = fields.Float(
        string='Percentual de Receita Bruta Acumulada',
        help='Percentual decorrente da receita bruta acumulada a ser aplicado\
        sobre a receita mensal.')

    l10n_br_environment = fields.Selection(
        [('test', 'Test'),
         ('production', 'Production')],
        string='Environment',
        default='production'
    )

    @api.onchange('payment_type')
    def _compute_tax_identification(self):
        for item in self:
            if item.payment_type not in ('05', '06', '07', '09'):
                continue
            return TAX_IDENTIFICATION.get(item.payment_type)
