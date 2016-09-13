# -*- coding: utf-8 -*-
# © 2013 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from openerp import models, fields, api, _
from openerp.addons import decimal_precision as dp
from openerp.exceptions import RedirectWarning

from odoo.addons.br_account.models.product import PRODUCT_ORIGIN


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    #TODO aqui vai ser complicado
    #@api.one
    #@api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id')
    #def _compute_amount(self):
        #self.icms_base = 0.0
        #self.icms_base_other = 0.0
        #self.icms_value = 0.0
        #self.icms_st_base = 0.0
        #self.icms_st_value = 0.0
        #self.ipi_base = sum(line.ipi_base for line in self.invoice_line_ids)
        #self.ipi_base_other = sum(
        #    line.ipi_base_other for line in self.invoice_line_ids)
        #self.ipi_value = sum(line.ipi_value for line in self.invoice_line_ids)
        #self.pis_base = sum(line.pis_base for line in self.invoice_line_ids)
        #self.pis_value = sum(line.pis_value for line in self.invoice_line_ids)
        #self.cofins_base = sum(
            #line.cofins_base for line in self.invoice_line_ids)
        #self.cofins_value = sum(
        #    line.cofins_value for line in self.invoice_line_ids)
        #self.ii_value = sum(line.ii_value for line in self.invoice_line_ids)
        #self.amount_discount = sum(
            #line.discount_value for line in self.invoice_line_ids)
        #self.amount_insurance = sum(
            #line.insurance_value for line in self.invoice_line_ids)
        #self.amount_costs = sum(
            #line.other_costs_value for line in self.invoice_line_ids)
        #self.amount_freight = sum(
            #line.freight_value for line in self.invoice_line_ids)
        #self.amount_total_taxes = sum(
            #line.total_taxes for line in self.invoice_line_ids)
        #self.amount_gross = sum(
            #line.price_gross for line in self.invoice_line_ids)
        #self.amount_tax_discount = 0.0
        #self.amount_untaxed = sum(
            #line.price_total for line in self.invoice_line_ids)
        #self.amount_tax = sum(tax.amount
        #                      for tax in self.tax_line_ids)
        #self.amount_total = self.amount_tax + self.amount_untaxed + \
            #self.amount_costs + self.amount_insurance + self.amount_freight

        #for line in self.invoice_line_ids:
            #if line.icms_cst not in (
             #       '101', '102', '201', '202', '300', '500'):
              #  self.icms_base += line.icms_base
                #self.icms_base_other += line.icms_base_other
                #self.icms_value += line.icms_value
            #else:
                #self.icms_base += 0.00
                #self.icms_base_other += 0.00
                #self.icms_value += 0.00
            #self.icms_st_base += line.icms_st_base
            #self.icms_st_value += line.icms_st_value

    @api.model
    def _default_fiscal_document(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.fiscal_document_for_product_id

    @api.one
    @api.depends('invoice_line_ids.cfop_id')
    def _compute_cfops(self):
        lines = self.env['l10n_br_account_product.cfop']
        for line in self.invoice_line_ids:
            if line.cfop_id:
                lines |= line.cfop_id
        self.cfop_ids = (lines).sorted()

    date_hour_invoice = fields.Datetime(
        u'Data e hora de emissão', readonly=True,
        states={'draft': [('readonly', False)]},
        select=True, help="Deixe em branco para usar a data atual")
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Consumidor final')
    ], u'Operação com Consumidor final', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indica operação com Consumidor final.', default='0')
    ind_pres = fields.Selection([
        ('0', u'Não se aplica'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('9', u'Operação não presencial, outros'),
    ], u'Tipo de operação', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indicador de presença do comprador no\n'
             u'estabelecimento comercial no momento\n'
             u'da operação.', default='0')
    fiscal_document_id = fields.Many2one(
        'br_account.fiscal.document', 'Documento', readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document)
    fiscal_document_electronic = fields.Boolean(
        related='fiscal_document_id.electronic')
    fiscal_type = fields.Selection(
        [('service', 'Serviço'), ('product', 'Produto')],
        'Tipo Fiscal',
        required=True,
        default='product')
    nfe_purpose = fields.Selection(
        [('1', 'Normal'),
         ('2', 'Complementar'),
         ('3', 'Ajuste'),
         ('4', u'Devolução de Mercadoria')],
        'Finalidade da Emissão', readonly=True,
        states={'draft': [('readonly', False)]}, default='1')
    cfop_ids = fields.Many2many(
        'l10n_br_account_product.cfop', string='CFOP',
        copy=False, compute='_compute_cfops')
    # fiscal_document_related_ids = fields.One2many(
    #    'l10n_br_account_product.document.related', 'invoice_id',
    #    'Fiscal Document Related', readonly=True,
    #    states={'draft': [('readonly', False)]})
    carrier_name = fields.Char('Transportadora', size=32)
    vehicle_plate = fields.Char('Placa do Veiculo', size=7)
    vehicle_state_id = fields.Many2one('res.country.state', 'UF da Placa')
    vehicle_city_id = fields.Many2one(
        'res.state.city',
        'Municipio',
        domain="[('state_id', '=', vehicle_state_id)]")
    amount_untaxed = fields.Float(
        string='Untaxed',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    amount_tax = fields.Float(
        string='Tax',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    amount_total = fields.Float(
        string='Total',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    amount_gross = fields.Float(
        string='Vlr. Bruto',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)
    amount_discount = fields.Float(
        string='Desconto',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    icms_base = fields.Float(
        string='Base ICMS',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    icms_base_other = fields.Float(
        string='Base ICMS Outras',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        readonly=True)
    icms_value = fields.Float(
        string='Valor ICMS', digits=dp.get_precision('Account'),
        compute='_compute_amount', store=True)
    icms_st_base = fields.Float(
        string='Base ICMS ST',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    icms_st_value = fields.Float(
        string='Valor ICMS ST',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')
    ipi_base = fields.Float(
        string='Base IPI', store=True, digits=dp.get_precision('Account'),
        compute='_compute_amount')
    ipi_base_other = fields.Float(
        string="Base IPI Outras", store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    ipi_value = fields.Float(
        string='Valor IPI', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    pis_base = fields.Float(
        string='Base PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    pis_value = fields.Float(
        string='Valor PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    cofins_base = fields.Float(
        string='Base COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    cofins_value = fields.Float(
        string='Valor COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)
    ii_value = fields.Float(
        string='Valor II', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True)
    weight = fields.Float(
        string='Gross weight', states={'draft': [('readonly', False)]},
        help="The gross weight in Kg.", readonly=True)
    weight_net = fields.Float(
        'Net weight', help="The net weight in Kg.",
        readonly=True, states={'draft': [('readonly', False)]})
    number_of_packages = fields.Integer(
        'Volume', readonly=True, states={'draft': [('readonly', False)]})
    kind_of_packages = fields.Char(
        'Espécie', size=60, readonly=True, states={
            'draft': [
                ('readonly', False)]})
    brand_of_packages = fields.Char(
        'Brand', size=60, readonly=True, states={
            'draft': [
                ('readonly', False)]})
    notation_of_packages = fields.Char(
        'Numeração', size=60, readonly=True, states={
            'draft': [
                ('readonly', False)]})
    amount_insurance = fields.Float(
        string='Valor do Seguro', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_freight = fields.Float(
        string='Valor do Frete', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_costs = fields.Float(
        string='Outros Custos', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_total_taxes = fields.Float(
        string='Total de Tributos',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    @api.multi
    def action_cancel_draft(self):
        result = super(AccountInvoice, self).action_cancel_draft()
        self.write({
            'internal_number': False,
            'nfe_access_key': False,
            'nfe_status': False,
            'nfe_date': False,
            'nfe_export_date': False})
        return result

    @api.onchange('fiscal_document_id')
    def onchange_fiscal_document_id(self):
        if self.fiscal_type == 'product':
            if self.issuer == '0':
                series = [doc_serie for doc_serie in
                          self.company_id.document_serie_product_ids if
                          doc_serie.fiscal_document_id.id ==
                          self.fiscal_document_id.id and doc_serie.active]

                if not series:
                    action = self.env.ref(
                        'l10n_br_account_new.'
                        'action_l10n_br_account_document_serie_form')
                    msg = _(u'Você deve ser uma série de documento fiscal'
                            u'para este documento fiscal.')
                    raise RedirectWarning(
                        msg, action.id, _(u'Criar uma nova série'))
                self.document_serie_id = series[0]

    @api.multi
    def action_date_assign(self):
        res = super(AccountInvoice, self).action_date_assign()
        for invoice in self:
            if not invoice.date_hour_invoice:
                invoice.write({
                    'date_hour_invoice': datetime.now(),
                    'date_invoice': datetime.now().date()
                })
        return res

    @api.multi
    def button_reset_taxes(self):
        result = super(AccountInvoice, self).button_reset_taxes()
        ait = self.env['account.invoice.tax']
        for invoice in self:
            invoice.read()
            costs = []
            company = invoice.company_id
            if invoice.amount_insurance:
                costs.append((company.insurance_tax_id,
                              invoice.amount_insurance))
            if invoice.amount_freight:
                costs.append((company.freight_tax_id,
                              invoice.amount_freight))
            if invoice.amount_costs:
                costs.append((company.other_costs_tax_id,
                              invoice.amount_costs))
            for tax, cost in costs:
                ait_id = ait.search([
                    ('invoice_id', '=', invoice.id),
                    ('tax_code_id', '=', tax.id),
                ])
                vals = {
                    'tax_amount': cost,
                    'name': tax.name,
                    'sequence': 1,
                    'invoice_id': invoice.id,
                    'manual': True,
                    'base_amount': cost,
                    'base_code_id': tax.base_code_id.id,
                    'tax_code_id': tax.tax_code_id.id,
                    'amount': cost,
                    'base': cost,
                    'account_analytic_id':
                        tax.account_analytic_collected_id.id or False,
                    'account_id': tax.account_paid_id.id,
                }
                if ait_id:
                    ait_id.write(vals)
                else:
                    ait.create(vals)
        return result


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'freight_value',
                 'insurance_value', 'other_costs_value',
                 'invoice_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_ids.compute_all(
            price, self.currency_id, self.quantity, product=self.product_id,
            partner=self.invoice_id.partner_id)
        self.price_subtotal = taxes['total_excluded']
        self.price_total = taxes['total_included']
        self.price_gross = taxes['base']
        self.discount_value = 0.0

    date_invoice = fields.Datetime(
        'Invoice Date', readonly=True, states={'draft': [('readonly', False)]},
        select=True, help="Keep empty to use the current date")
    cfop_id = fields.Many2one('l10n_br_account_product.cfop', 'CFOP')
    # fiscal_classification_id = fields.Many2one(
    #    'account.product.fiscal.classification', 'Classificação Fiscal')
    fci = fields.Char('FCI do Produto', size=36)
    # import_declaration_ids = fields.One2many(
    #    'l10n_br_account_product.import.declaration',
    #    'invoice_line_id', u'Declaração de Importação')
    product_type = fields.Selection(
        [('product', 'Produto'), ('service', u'Serviço')],
        'Tipo do Produto', required=True, default='product')
    discount_value = fields.Float(
        string='Vlr. desconto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    price_gross = fields.Float(
        string='Vlr. Bruto', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    price_subtotal = fields.Float(
        string='Subtotal', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    price_total = fields.Float(
        string='Total', store=True, compute='_compute_price',
        digits=dp.get_precision('Account'))
    total_taxes = fields.Float(
        string='Total de Tributos', requeried=True, default=0.00,
        digits=dp.get_precision('Account'))
    tax_icms_id = fields.Many2one('account.tax', string="ICMS",
                                  domain=[('domain', '=', 'icms')])

    icms_manual = fields.Boolean('ICMS Manual?', default=False)
    icms_origin = fields.Selection(PRODUCT_ORIGIN, 'Origem', default='0')
    icms_base_type = fields.Selection(
        [('0', 'Margem Valor Agregado (%)'), ('1', 'Pauta (valor)'),
         ('2', 'Preço Tabelado Máximo (valor)'),
         ('3', 'Valor da Operação')],
        'Tipo Base ICMS', required=True, default='0')
    icms_base = fields.Float('Base ICMS', required=True,
                             digits=dp.get_precision('Account'), default=0.00)
    icms_base_other = fields.Float(
        'Base ICMS Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_value = fields.Float(
        'Valor ICMS', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_percent = fields.Float(
        'Perc ICMS', digits=dp.get_precision('Discount'), default=0.00)
    icms_percent_reduction = fields.Float(
        'Perc Redução de Base ICMS', digits=dp.get_precision('Discount'),
        default=0.00)
    icms_st_base_type = fields.Selection(
        [('0', 'Preço tabelado ou máximo  sugerido'),
         ('1', 'Lista Negativa (valor)'),
         ('2', 'Lista Positiva (valor)'), ('3', 'Lista Neutra (valor)'),
         ('4', 'Margem Valor Agregado (%)'), ('5', 'Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')
    icms_st_value = fields.Float(
        'Valor ICMS ST', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_base = fields.Float(
        'Base ICMS ST', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_st_percent = fields.Float(
        '% ICMS ST', digits=dp.get_precision('Discount'),
        default=0.00)
    icms_st_percent_reduction = fields.Float(
        '% Red. Base ST',
        digits=dp.get_precision('Discount'), default=0.00)
    icms_st_mva = fields.Float(
        'MVA Ajustado ST',
        digits=dp.get_precision('Discount'), default=0.00)
    icms_st_base_other = fields.Float(
        'Base ICMS ST Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    icms_cst = fields.Char('CST ICMS', size=10)
    icms_percent_credit = fields.Float(u"% Cŕedito ICMS")
    icms_value_credit = fields.Float(u"Valor de Crédito")
    origem = fields.Selection(
        [('0', '0 - Nacional'),
         ('1', '1 - Estrangeira - Importação direta'),
         ('2', '2 - Estrangeira - Adquirida no mercado interno'),
         ('3', '3 - Nacional, mercadoria ou bem com Conteúdo de Importação \
superior a 40% \e inferior ou igual a 70%'),
         ('4', '4 - Nacional, cuja produção tenha sido feita em conformidade \
com os processos produtivos básicos de que tratam as \
legislações citadas nos Ajustes'),
         ('5', '5 - Nacional, mercadoria ou bem com Conteúdo de Importação \
inferior ou igual a 40%'),
         ('6', '6 - Estrangeira - Importação direta, sem similar nacional, \
constante em lista da CAMEX e gás natural'),
         ('7', '7 - Estrangeira - Adquirida no mercado interno, sem similar \
nacional, constante lista CAMEX e gás natural'),
         ('8', '8 - Nacional, mercadoria ou bem com Conteúdo de Importação \
superior a 70%')],
        u'Origem da mercadoria')

    tax_issqn_id = fields.Many2one('account.tax', string="ISSQN",
                                   domain=[('domain', '=', 'issqn')])
    issqn_manual = fields.Boolean('ISSQN Manual?', default=False)
    issqn_type = fields.Selection(
        [('N', 'Normal'), ('R', 'Retida'),
         ('S', 'Substituta'), ('I', 'Isenta')], 'Tipo do ISSQN',
        required=True, default='N')
    service_type_id = fields.Many2one(
        'l10n_br_account.service.type', 'Tipo de Serviço')
    issqn_base = fields.Float(
        'Base ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    issqn_percent = fields.Float(
        'Perc ISSQN', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    issqn_value = fields.Float(
        'Valor ISSQN', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    tax_ipi_id = fields.Many2one('account.tax', string="IPI",
                                  domain=[('domain', '=', 'ipi')])
    ipi_manual = fields.Boolean('IPI Manual?', default=False)
    ipi_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do IPI', required=True, default='percent')
    ipi_base = fields.Float(
        'Base IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_base_other = fields.Float(
        'Base IPI Outras', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_value = fields.Float(
        'Valor IPI', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ipi_percent = fields.Float(
        'Perc IPI', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    ipi_cst = fields.Char('CST IPI', size=10)
    tax_pis_id = fields.Many2one('account.tax', string="PIS",
                                  domain=[('domain', '=', 'pis')])
    pis_manual = fields.Boolean('PIS Manual?', default=False)
    pis_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do PIS', required=True, default='percent')
    pis_base = fields.Float('Base PIS', required=True,
                            digits=dp.get_precision('Account'), default=0.00)
    pis_base_other = fields.Float(
        'Base PIS Outras', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_value = fields.Float(
        'Valor PIS', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_percent = fields.Float(
        'Perc PIS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    pis_cst = fields.Char('CST PIS', size=10)
    pis_st_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do PIS ST', required=True, default='percent')
    pis_st_base = fields.Float(
        'Base PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_st_percent = fields.Float(
        'Perc PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    pis_st_value = fields.Float(
        'Valor PIS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    tax_cofins_id = fields.Many2one('account.tax', string="COFINS",
                                  domain=[('domain', '=', 'cofins')])
    cofins_manual = fields.Boolean('COFINS Manual?', default=False)
    cofins_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do COFINS', required=True, default='percent')
    cofins_base = fields.Float(
        'Base COFINS',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00)
    cofins_base_other = fields.Float(
        'Base COFINS Outras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    cofins_value = fields.Float(
        'Valor COFINS', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    cofins_percent = fields.Float(
        'Perc COFINS', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    cofins_cst = fields.Char('CST PIS')
    cofins_st_type = fields.Selection(
        [('percent', 'Percentual'), ('quantity', 'Em Valor')],
        'Tipo do COFINS ST', required=True, default='percent')
    cofins_st_base = fields.Float(
        'Base COFINS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    cofins_st_percent = fields.Float(
        'Perc COFINS ST', required=True, digits=dp.get_precision('Discount'),
        default=0.00)
    cofins_st_value = fields.Float(
        'Valor COFINS ST', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    tax_ii_id = fields.Many2one('account.tax', string="II",
                                  domain=[('domain', '=', 'ii')])
    ii_base = fields.Float(
        'Base II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_value = fields.Float(
        'Valor II', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_iof = fields.Float(
        'Valor IOF', required=True, digits=dp.get_precision('Account'),
        default=0.00)
    ii_customhouse_charges = fields.Float(
        'Depesas Atuaneiras', required=True,
        digits=dp.get_precision('Account'), default=0.00)
    insurance_value = fields.Float(
        'Valor do Seguro', digits=dp.get_precision('Account'), default=0.00)
    other_costs_value = fields.Float(
        'Outros Custos', digits=dp.get_precision('Account'), default=0.00)
    freight_value = fields.Float(
        'Frete', digits=dp.get_precision('Account'), default=0.00)
    fiscal_comment = fields.Text(u'Observação Fiscal')

    @api.multi
    def write(self, vals):

        res = super(AccountInvoiceLine, self).write(vals)
        #for item in self:
        #    item.invoice_line_tax_ids = item.tax_icms_id | item.tax_pis_id | item.tax_cofins_id | item.tax_ipi_id
        return res

    @api.onchange('tax_icms_id')
    def _onchange_tax_icms_id(self):
        if self.tax_icms_id:
            self.icms_percent = self.tax_icms_id.amount
            self.icms_cst = self.tax_icms_id.cst

    @api.onchange('tax_pis_id')
    def _onchange_tax_pis_id(self):
        if self.tax_pis_id:
            self.pis_percent = self.tax_pis_id.amount
            self.pis_cst = self.tax_ipi_id.cst

    @api.onchange('tax_cofins_id')
    def _onchange_tax_cofins_id(self):
        if self.tax_cofins_id:
            self.cofins_percent = self.tax_cofins_id.amount
            self.cofins_cst = self.tax_ipi_id.cst

    @api.onchange('tax_ipi_id')
    def _onchange_tax_ipi_id(self):
        if self.tax_ipi_id:
            self.ipi_percent = self.tax_ipi_id.amount
            self.ipi_cst = self.tax_ipi_id.cst


    def _amount_tax_icms(self, tax=None):
        result = {
            'icms_base': tax.get('total_base', 0.0),
            'icms_base_other': tax.get('total_base_other', 0.0),
            'icms_value': tax.get('amount', 0.0),
            'icms_percent': tax.get('percent', 0.0) * 100,
            'icms_percent_reduction': tax.get('base_reduction') * 100,
            'icms_base_type': tax.get('icms_base_type', '0'),
        }
        return result

    def _amount_tax_icmsst(self, tax=None):
        result = {
            'icms_st_value': tax.get(
                'amount',
                0.0),
            'icms_st_base': tax.get(
                'total_base',
                0.0),
            'icms_st_percent': tax.get(
                'icms_st_percent',
                0.0) * 100,
            'icms_st_percent_reduction': tax.get(
                'icms_st_percent_reduction',
                0.0) * 100,
            'icms_st_mva': tax.get(
                'amount_mva',
                0.0) * 100,
            'icms_st_base_other': tax.get(
                'icms_st_base_other',
                0.0),
            'icms_st_base_type': tax.get(
                'icms_st_base_type',
                '4')}
        return result

    def _amount_tax_ipi(self, tax=None):
        result = {
            'ipi_type': tax.get('type'),
            'ipi_base': tax.get('total_base', 0.0),
            'ipi_value': tax.get('amount', 0.0),
            'ipi_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_cofins(self, tax=None):
        result = {
            'cofins_base': tax.get('total_base', 0.0),
            'cofins_base_other': tax.get('total_base_other', 0.0),
            'cofins_value': tax.get('amount', 0.0),
            'cofins_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_cofinsst(self, tax=None):
        result = {
            'cofins_st_type': 'percent',
            'cofins_st_base': 0.0,
            'cofins_st_percent': 0.0,
            'cofins_st_value': 0.0,
        }
        return result

    def _amount_tax_pis(self, tax=None):
        result = {
            'pis_base': tax.get('total_base', 0.0),
            'pis_base_other': tax.get('total_base_other', 0.0),
            'pis_value': tax.get('amount', 0.0),
            'pis_percent': tax.get('percent', 0.0) * 100,
        }
        return result

    def _amount_tax_pisst(self, tax=None):
        result = {
            'pis_st_type': 'percent',
            'pis_st_base': 0.0,
            'pis_st_percent': 0.0,
            'pis_st_value': 0.0,
        }
        return result

    def _amount_tax_ii(self, tax=None):
        result = {
            'ii_base': 0.0,
            'ii_value': 0.0,
        }
        return result

    def _amount_tax_issqn(self, tax=None):

        # TODO deixar dinamico a definição do tipo do ISSQN
        # assim como todos os impostos
        issqn_type = 'N'
        if not tax.get('amount'):
            issqn_type = 'I'

        result = {
            'issqn_type': issqn_type,
            'issqn_base': tax.get('total_base', 0.0),
            'issqn_percent': tax.get('percent', 0.0) * 100,
            'issqn_value': tax.get('amount', 0.0),
        }
        return result

    @api.multi
    def _get_tax_codes(self, product_id, fiscal_position_id, taxes):
        result = {}
        ctx = dict(self.env.context)
        ctx.update({'use_domain': ('use_invoice', '=', True)})

        product = self.env['product.product'].browse(product_id)
        ctx.update({'fiscal_type': product.fiscal_type})
        result['cfop_id'] = fiscal_position_id.cfop_id.id

        # result['icms_cst_id'] = tax_codes.get('icms')
        # result['ipi_cst_id'] = tax_codes.get('ipi')
        # result['pis_cst_id'] = tax_codes.get('pis')
        # result['cofins_cst_id'] = tax_codes.get('cofins')
        return result

    @api.multi
    def _validate_taxes(self, values):
        """Verifica se o valor dos campos dos impostos estão sincronizados
        com os impostos do Odoo"""
        context = self.env.context

        price_unit = values.get('price_unit', 0.0) or self.price_unit
        discount = values.get('discount', 0.0)
        insurance_value = values.get(
            'insurance_value', 0.0) or self.insurance_value
        freight_value = values.get(
            'freight_value', 0.0) or self.freight_value
        other_costs_value = values.get(
            'other_costs_value', 0.0) or self.other_costs_value
        tax_ids = []
        if values.get('invoice_line_tax_ids'):
            tax_ids = values.get('invoice_line_tax_ids', [[6, 0, []]])[
                0][2] or self.invoice_line_tax_ids.ids
        partner_id = values.get('partner_id') or self.partner_id.id
        product_id = values.get('product_id') or self.product_id.id
        quantity = values.get('quantity') or self.quantity
        fiscal_position_id = values.get(
            'fiscal_position_id') or self.fiscal_position_id.id

        if not product_id or not quantity or not fiscal_position_id:
            return {}

        result = {
            'product_type': 'product',
            'service_type_id': None,
            'fiscal_classification_id': None,
            'fci': None,
        }

        if self:
            partner = self.invoice_id.partner_id
        else:
            partner = self.env['res.partner'].browse(partner_id)

        taxes = self.env['account.tax'].browse(tax_ids)
        fiscal_position_id = self.env['account.fiscal.position'].browse(
            fiscal_position_id)

        price = price_unit * (1 - discount / 100.0)

        if product_id:
            product = self.pool.get('product.product').browse(
                self._cr, self._uid, product_id, context=context)
            if product.type == 'service':
                result['product_type'] = 'service'
                result['service_type_id'] = product.service_type_id.id
            else:
                result['product_type'] = 'product'
            if product.fiscal_classification_id:
                result['fiscal_classification_id'] = \
                    product.fiscal_classification_id.id

            if product.fci:
                result['fci'] = product.fci

            result['icms_origin'] = product.origin

        taxes_calculed = taxes.compute_all(
            price, currency=None, quantity=quantity, product=product,
            partner=partner)

        result['total_taxes'] = taxes_calculed['total_taxes']

        for tax in taxes_calculed['taxes']:
            try:
                amount_tax = getattr(
                    self, '_amount_tax_%s' % tax.get('domain', ''))
                result.update(amount_tax(tax))
            except AttributeError:
                # Caso não exista campos especificos dos impostos
                # no documento fiscal, os mesmos são calculados.
                continue

        result.update(self._get_tax_codes(
            product_id, fiscal_position_id, taxes))
        return result
