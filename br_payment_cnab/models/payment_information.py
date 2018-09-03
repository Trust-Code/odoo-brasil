# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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
        ], string=u'Movimentation Purpose')

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
        ], string=u'Movimentation TED Purpose')

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
         ('08', 'FGTS')],
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

    service_type = fields.Selection(
        [('03', 'Bloqueto Eletronico'),
         ('10', 'Pagamento de dividendos'),
         ('14', 'Consulta de tributos a pagar DETRAN com RENAVAM'),
         ('20', 'Provider/Fees Payment'),
         ('22', 'Bill and tax payment'),
         ('29', 'Alegacao do sacado'),
         ('50', 'Pagamento de sinistros segurados'),
         ('60', 'Pagamento Despesas Viajante em Transito'),
         ('70', 'Pagamento Autorizado'),
         ('75', 'Pagamento Credenciados'),
         ('80', 'Pagamento Representantes / Vendedores Autorizados'),
         ('90', 'Pagamento Beneficios'),
         ('98', 'Pagamentos Diversos')],
        string='Service Type')

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
         ('17', 'GPS (Guia da Previdência Social)')],
        string="Tax Identification",
        compute='_compute_tax_identification')

    barcode = fields.Char('Barcode')

    numero_referencia = fields.Char('Número de Referência')

    percentual_receita_bruta_acumulada = fields.Float(
        string='Percentual de Receita Bruta Acumulada',
        help='Percentual decorrente da receita bruta acumulada a ser aplicado\
        sobre a receita mensal.')

    @api.onchange('payment_type')
    def _compute_tax_identification(self):
        for item in self:
            if item.payment_type not in ('05', '06', '07'):
                continue
            elif item.payment_type == '05':
                item.tax_identification = '17'
            elif item.payment_type == '06':
                item.tax_identification = '16'
            else:
                item.tax_identification = '18'
