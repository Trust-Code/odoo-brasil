from odoo import api, fields, models
from .cst import CST_ICMS
from .cst import CSOSN_SIMPLES
from .cst import CST_IPI
from .cst import CST_PIS_COFINS


class AccountFiscalPositionTaxRule(models.Model):
    _name = 'account.fiscal.position.tax.rule'
    _description = "Regras de Impostos"
    _order = 'sequence'

    sequence = fields.Integer(string=u"Sequência")
    name = fields.Char(string=u"Descrição", size=100)
    domain = fields.Selection([('icms', 'ICMS'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('csll', 'CSLL'),
                               ('irrf', 'IRRF'),
                               ('inss', 'INSS'),
                               ('outros', 'Outros')], string=u"Tipo")
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string=u"Posição Fiscal")

    state_ids = fields.Many2many('res.country.state', string=u"Estado Destino",
                                 domain=[('country_id.code', '=', 'BR')])
    # fiscal_category_ids = fields.Many2many(
    #     'br_account.fiscal.category', string=u"Categorias Fiscais")
    tipo_produto = fields.Selection([('product', u'Produto'),
                                     ('service', u'Serviço')],
                                    string=u"Tipo produto", default="product")

    # product_fiscal_classification_ids = fields.Many2many(
    #     'product.fiscal.classification', string=u"Classificação Fiscal",
    #     relation="account_fiscal_position_tax_rule_prod_fiscal_clas_relation")

    cst_icms = fields.Selection(CST_ICMS, string=u"CST ICMS")
    csosn_icms = fields.Selection(CSOSN_SIMPLES, string=u"CSOSN ICMS")
    cst_pis = fields.Selection(CST_PIS_COFINS, string=u"CST PIS")
    cst_cofins = fields.Selection(CST_PIS_COFINS, string=u"CST COFINS")
    cst_ipi = fields.Selection(CST_IPI, string=u"CST IPI")
    cfop_id = fields.Many2one('br_account.cfop', string=u"CFOP")
    tax_id = fields.Many2one('account.tax', string=u"Imposto")
    tax_icms_st_id = fields.Many2one('account.tax', string=u"ICMS ST",
                                     domain=[('domain', '=', 'icmsst')])
    icms_aliquota_credito = fields.Float(string=u"% Crédito de ICMS")
    incluir_ipi_base = fields.Boolean(string=u"Incl. IPI na base ICMS")
    reducao_icms = fields.Float(string=u"Redução de base")
    reducao_icms_st = fields.Float(string=u"Redução de base ST")
    reducao_ipi = fields.Float(string=u"Redução de base IPI")
    l10n_br_issqn_deduction = fields.Float(string="% Dedução de base ISSQN")
    aliquota_mva = fields.Float(string=u"Alíquota MVA")
    icms_st_aliquota_deducao = fields.Float(
        string=u"% ICMS Próprio",
        help=u"Alíquota interna ou interestadual aplicada \
         sobre o valor da operação para deduzir do ICMS ST - Para empresas \
         do Simples Nacional ou usado em casos onde existe apenas ST sem ICMS")
    tem_difal = fields.Boolean(string="Aplicar Difal?")
    tax_icms_inter_id = fields.Many2one(
        'account.tax', help=u"Alíquota utilizada na operação Interestadual",
        string=u"ICMS Inter", domain=[('domain', '=', 'icms_inter')])
    tax_icms_intra_id = fields.Many2one(
        'account.tax', help=u"Alíquota interna do produto no estado destino",
        string=u"ICMS Intra", domain=[('domain', '=', 'icms_intra')])
    tax_icms_fcp_id = fields.Many2one(
        'account.tax', string=u"% FCP", domain=[('domain', '=', 'fcp')])


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    edoc_policy = fields.Selection(
      [('directly', 'Emitir agora'),
        ('after_payment', 'Emitir após pagamento'),
        ('manually', 'Manualmente')], string="Nota Eletrônica", default='directly')

    journal_id = fields.Many2one(
        'account.journal', string=u"Diário Contábil",
        help=u"Diário Contábil a ser utilizado na fatura.", copy=True)
    account_id = fields.Many2one(
        'account.account', string=u"Conta Contábil",
        help=u"Conta Contábil a ser utilizada na fatura.", copy=True)
    # fiscal_observation_ids = fields.Many2many(
    #     'br_account.fiscal.observation', string=u"Mensagens Doc. Eletrônico",
    #     copy=True)
    note = fields.Text(u'Observações')

    # product_serie_id = fields.Many2one(
    #     'br_account.document.serie', string=u'Série Produto',
    #     domain="[('fiscal_document_id', '=', product_document_id)]", copy=True)
    # product_document_id = fields.Many2one(
    #     'br_account.fiscal.document', string='Documento Produto', copy=True)

    # service_serie_id = fields.Many2one(
    #     'br_account.document.serie', string=u'Série Serviço',
    #     domain="[('fiscal_document_id', '=', service_document_id)]",
    #     copy=True)
    # service_document_id = fields.Many2one(
    #     'br_account.fiscal.document', string='Documento Serviço', copy=True)

    icms_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras ICMS", domain=[('domain', '=', 'icms')], copy=True)
    ipi_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras IPI", domain=[('domain', '=', 'ipi')], copy=True)
    pis_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras PIS", domain=[('domain', '=', 'pis')], copy=True)
    cofins_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras COFINS", domain=[('domain', '=', 'cofins')],
        copy=True)
    issqn_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras ISSQN", domain=[('domain', '=', 'issqn')], copy=True)
    ii_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras II", domain=[('domain', '=', 'ii')], copy=True)
    irrf_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras IRRF", domain=[('domain', '=', 'irrf')], copy=True)
    csll_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras CSLL", domain=[('domain', '=', 'csll')], copy=True)
    inss_tax_rule_ids = fields.One2many(
        'account.fiscal.position.tax.rule', 'fiscal_position_id',
        string=u"Regras INSS", domain=[('domain', '=', 'inss')], copy=True)
    fiscal_type = fields.Selection([('saida', 'Saída'),
                                    ('entrada', 'Entrada'),
                                    ('import', 'Entrada Importação')],
                                   string=u"Tipo da posição", copy=True)

    finalidade_emissao = fields.Selection(
        [('1', u'Normal'),
         ('2', u'Complementar'),
         ('3', u'Ajuste'),
         ('4', u'Devolução')],
        u'Finalidade', help=u"Finalidade da emissão de NFe", default="1")
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Sim')
    ], u'Consumidor final?',
        help=u'Indica operação com Consumidor final. Se não utilizado usa\
        a seguinte regra:\n 0 - Normal quando pessoa jurídica\n1 - Consumidor \
        Final quando for pessoa física')
    ind_pres = fields.Selection([
        ('0', u'Não se aplica'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('5', u'Operação presencial, fora do estabelecimento'),
        ('9', u'Operação não presencial, outros'),
    ], u'Tipo de operação',
        help=u'Indicador de presença do comprador no\n'
             u'estabelecimento comercial no momento\n'
             u'da operação.', default='0')
