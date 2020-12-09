from odoo import api, fields, models
from .cst import CST_ICMS
from .cst import CSOSN_SIMPLES
from .cst import CST_IPI
from .cst import CST_PIS_COFINS

class AccountFiscalPositionTaxRule(models.Model):
    _name = 'account.fiscal.position.tax.rule'
    _description = "Regras de Impostos"
    _order = 'sequence'

    sequence = fields.Integer(string="Sequência")


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    edoc_policy = fields.Selection(
      [('directly', 'Emitir agora'),
        ('after_payment', 'Emitir após pagamento'),
        ('manually', 'Manualmente')], string="Nota Eletrônica", default='directly')

    journal_id = fields.Many2one(
        'account.journal', string="Diário Contábil",
        help="Diário Contábil a ser utilizado na fatura.", copy=True)
    account_id = fields.Many2one(
        'account.account', string="Conta Contábil",
        help="Conta Contábil a ser utilizada na fatura.", copy=True)
    # fiscal_observation_ids = fields.Many2many(
    #     'br_account.fiscal.observation', string=u"Mensagens Doc. Eletrônico",
    #     copy=True)
    note = fields.Text('Observações')

    apply_tax_ids = fields.Many2many('account.tax', string='Impostos a aplicar')
    csosn_icms = fields.Selection(CSOSN_SIMPLES, string="CSOSN ICMS")
    icms_aliquota_credito = fields.Float(string="% Crédito de ICMS")

    fiscal_type = fields.Selection([('saida', 'Saída'),
                                    ('entrada', 'Entrada'),
                                    ('import', 'Entrada Importação')],
                                   string="Tipo da posição", copy=True)

    serie_nota_fiscal = fields.Char('Série da NFe')
    finalidade_emissao = fields.Selection(
        [('1', 'Normal'),
         ('2', 'Complementar'),
         ('3', 'Ajuste'),
         ('4', 'Devolução')],
        'Finalidade', help=u"Finalidade da emissão de NFe", default="1")
    ind_final = fields.Selection([
        ('0', 'Não'),
        ('1', 'Sim')
    ], 'Consumidor final?',
        help='Indica operação com Consumidor final. Se não utilizado usa\
        a seguinte regra:\n 0 - Normal quando pessoa jurídica\n1 - Consumidor \
        Final quando for pessoa física')
    ind_pres = fields.Selection([
        ('0', 'Não se aplica'),
        ('1', 'Operação presencial'),
        ('2', 'Operação não presencial, pela Internet'),
        ('3', 'Operação não presencial, Teleatendimento'),
        ('4', 'NFC-e em operação com entrega em domicílio'),
        ('5', 'Operação presencial, fora do estabelecimento'),
        ('9', 'Operação não presencial, outros'),
    ], 'Tipo de operação',
        help='Indicador de presença do comprador no\n'
             'estabelecimento comercial no momento\n'
             'da operação.', default='0')

    @api.model
    def _get_fpos_by_region(self, country_id=False, state_id=False,
                            zipcode=False, vat_required=False):
        fpos = super(AccountFiscalPosition, self)._get_fpos_by_region(
            country_id=country_id, state_id=state_id, zipcode=zipcode,
            vat_required=vat_required)
        type_inv = self.env.context.get('type', False)
        supplier = self.env.context.get('search_default_supplier', False)
        customer = self.env.context.get('search_default_customer', False)
        if type_inv == 'in_invoice' or supplier:
            type_inv = 'entrada'
        elif type_inv == 'out_invoice' or customer:
            type_inv = 'saida'
        fpos = self.search([('auto_apply', '=', True),
                            ('fiscal_type', '=', type_inv)], limit=1)
        return fpos