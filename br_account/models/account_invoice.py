# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        lines = self.invoice_line_ids
        self.icms_base = sum(l.icms_base for l in lines)
        self.icms_base_other = sum(l.icms_base_other for l in lines)
        self.icms_value = sum(l.icms_value for l in lines)
        self.icms_st_base = sum(l.icms_st_base for l in lines)
        self.icms_st_value = sum(l.icms_st_value for l in lines)
        self.issqn_base = sum(l.issqn_base for l in lines)
        self.issqn_value = sum(l.issqn_value for l in lines)
        self.ipi_base = sum(l.ipi_base for l in lines)
        self.ipi_base_other = sum(l.ipi_base_other for l in lines)
        self.ipi_value = sum(l.ipi_value for l in lines)
        self.pis_base = sum(l.pis_base for l in lines)
        self.pis_value = sum(l.pis_value for l in lines)
        self.cofins_base = sum(l.cofins_base for l in lines)
        self.cofins_value = sum(l.cofins_value for l in lines)
        self.ii_value = sum(l.ii_value for l in lines)
        self.amount_gross = sum(l.price_gross for l in lines)
        self.amount_discount = sum(l.discount_value for l in lines)
        self.amount_insurance = sum(l.insurance_value for l in lines)
        self.amount_costs = sum(l.other_costs_value for l in lines)
        self.amount_estimated_tax = sum(l.estimated_taxes for l in lines)

    @api.one
    @api.depends('move_id.line_ids')
    def _compute_receivables(self):
        receivable_lines = []
        for line in self.move_id.line_ids:
            if line.account_id.user_type_id.type == "receivable":
                receivable_lines.append(line.id)
        self.receivable_move_line_ids = self.env['account.move.line'].browse(
            list(set(receivable_lines)))

    @api.one
    @api.depends('move_id.line_ids')
    def _compute_payables(self):
        receivable_lines = []
        for line in self.move_id.line_ids:
            if line.account_id.user_type_id.type == "payable":
                receivable_lines.append(line.id)
        self.receivable_move_line_ids = self.env['account.move.line'].browse(
            list(set(receivable_lines)))

    @api.model
    def _default_fiscal_document(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.fiscal_document_for_product_id

    @api.model
    def _default_fiscal_document_serie(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.document_serie_id.id

    receivable_move_line_ids = fields.Many2many(
        'account.move.line', string='Receivable Move Lines',
        compute='_compute_receivables')

    payable_move_line_ids = fields.Many2many(
        'account.move.line', string='Payable Move Lines',
        compute='_compute_payables')

    issuer = fields.Selection(
        [('0', 'Terceiros'), ('1', u'Emissão própria')], 'Emitente',
        default='0', readonly=True, states={'draft': [('readonly', False)]})
    vendor_number = fields.Char(
        'Número NF Entrada', size=18, readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Número da Nota Fiscal do Fornecedor")
    vendor_serie = fields.Char(
        'Série NF Entrada', size=12, readonly=True,
        states={'draft': [('readonly', False)]},
        help=u"Série do número da Nota Fiscal do Fornecedor")
    document_serie_id = fields.Many2one(
        'br_account.document.serie', string=u'Série',
        domain="[('fiscal_document_id', '=', fiscal_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document_serie)
    fiscal_document_id = fields.Many2one(
        'br_account.fiscal.document', string='Documento', readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_document)
    is_eletronic = fields.Boolean(
        related='fiscal_document_id.electronic', type='boolean',
        store=True, string='Electronic')
    fiscal_comment = fields.Text(u'Observação Fiscal')

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
    issqn_base = fields.Float(
        string='Base ISSQN', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    issqn_value = fields.Float(
        string='Valor ISSQN', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
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
    amount_insurance = fields.Float(
        string='Valor do Seguro', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_costs = fields.Float(
        string='Outros Custos', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount')
    amount_estimated_tax = fields.Float(
        string='Total de Tributos',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount')

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        res = super(AccountInvoice, self).\
            finalize_invoice_move_lines(move_lines)

        count = 1
        for invoice_line in res:
            if self.payment_mode_id:
                line = invoice_line[2]
                line['ref'] = self.origin
                if line['name'] == '/':
                    line['name'] = "%02d" % count
                    count += 1
        return res

    @api.multi
    def get_taxes_values(self):
        for line in self.invoice_line_ids:
            line.invoice_line_tax_ids = line.tax_icms_id | line.tax_ipi_id | \
                line.tax_pis_id | line.tax_cofins_id | line.tax_issqn_id | \
                line.tax_ii_id

        return super(AccountInvoice, self).get_taxes_values()
