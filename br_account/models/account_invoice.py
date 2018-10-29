# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'br.localization.filtering']

    @api.one
    @api.depends('invoice_line_ids.price_subtotal',
                 'invoice_line_ids.price_total',
                 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        if not self.l10n_br_localization:
            return
        lines = self.invoice_line_ids
        self.l10n_br_total_tax = sum(l.l10n_br_price_tax for l in lines)
        self.l10n_br_icms_base = \
            sum(l.l10n_br_icms_base_calculo for l in lines)
        self.l10n_br_icms_value = sum(l.l10n_br_icms_valor for l in lines)
        self.l10n_br_icms_st_base = \
            sum(l.l10n_br_icms_st_base_calculo for l in lines)
        self.l10n_br_icms_st_value = \
            sum(l.l10n_br_icms_st_valor for l in lines)
        self.l10n_br_valor_icms_uf_remet = \
            sum(l.l10n_br_icms_uf_remet for l in lines)
        self.l10n_br_valor_icms_uf_dest = \
            sum(l.l10n_br_icms_uf_dest for l in lines)
        self.l10n_br_valor_icms_fcp_uf_dest = \
            sum(l.l10n_br_icms_fcp_uf_dest for l in lines)
        self.l10n_br_issqn_base = \
            sum(l.l10n_br_issqn_base_calculo for l in lines)
        self.l10n_br_issqn_value = \
            sum(abs(l.l10n_br_issqn_valor) for l in lines)
        self.l10n_br_ipi_base = sum(l.l10n_br_ipi_base_calculo for l in lines)
        self.l10n_br_ipi_value = sum(l.l10n_br_ipi_valor for l in lines)
        self.l10n_br_pis_base = sum(l.l10n_br_pis_base_calculo for l in lines)
        self.l10n_br_pis_value = sum(abs(l.l10n_br_pis_valor) for l in lines)
        self.l10n_br_cofins_base = \
            sum(l.l10n_br_cofins_base_calculo for l in lines)
        self.l10n_br_cofins_value = \
            sum(abs(l.l10n_br_cofins_valor) for l in lines)
        self.l10n_br_ii_base = sum(l.l10n_br_ii_base_calculo for l in lines)
        self.l10n_br_ii_value = sum(l.l10n_br_ii_valor for l in lines)
        self.l10n_br_csll_base = \
            sum(l.l10n_br_csll_base_calculo for l in lines)
        self.l10n_br_csll_value = sum(abs(l.l10n_br_csll_valor) for l in lines)
        self.l10n_br_irrf_base = \
            sum(l.l10n_br_irrf_base_calculo for l in lines)
        self.l10n_br_irrf_value = sum(abs(l.l10n_br_irrf_valor) for l in lines)
        self.l10n_br_inss_base = \
            sum(l.l10n_br_inss_base_calculo for l in lines)
        self.l10n_br_inss_value = sum(abs(l.l10n_br_inss_valor) for l in lines)

        # Retenções
        self.l10n_br_issqn_retention = sum(
            abs(l.l10n_br_issqn_valor)
            if l.l10n_br_issqn_valor < 0 else 0.0 for l in lines)
        self.l10n_br_pis_retention = sum(
            abs(l.l10n_br_pis_valor)
            if l.l10n_br_pis_valor < 0 else 0.0 for l in lines)
        self.l10n_br_cofins_retention = \
            sum(abs(l.l10n_br_cofins_valor)
                if l.l10n_br_cofins_valor < 0 else 0.0 for l in lines)
        self.l10n_br_csll_retention = sum(
            abs(l.l10n_br_csll_valor)
            if l.l10n_br_csll_valor < 0 else 0 for l in lines)
        self.l10n_br_irrf_retention = sum(
            abs(l.l10n_br_irrf_valor)
            if l.l10n_br_irrf_valor < 0 else 0.0 for l in lines)
        self.l10n_br_inss_retention = sum(
            abs(l.l10n_br_inss_valor)
            if l.l10n_br_inss_valor < 0 else 0.0 for l in lines)

        self.l10n_br_total_bruto = sum(l.l10n_br_valor_bruto for l in lines)
        self.l10n_br_total_desconto = \
            sum(l.l10n_br_valor_desconto for l in lines)
        self.l10n_br_total_tributos_federais = sum(
            l.l10n_br_tributos_estimados_federais for l in lines)
        self.l10n_br_total_tributos_estaduais = sum(
            l.l10n_br_tributos_estimados_estaduais for l in lines)
        self.l10n_br_total_tributos_municipais = sum(
            l.l10n_br_tributos_estimados_municipais for l in lines)
        self.l10n_br_total_tributos_estimados = sum(
            l.l10n_br_tributos_estimados for l in lines)
        # TOTAL
        self.amount_total = self.l10n_br_total_bruto - \
            self.l10n_br_total_desconto + self.l10n_br_total_tax
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = self.amount_total * sign
        self.amount_total_signed = self.amount_total * sign

    @api.one
    @api.depends('move_id.line_ids')
    def _compute_receivables(self):
        receivable_lines = []
        for line in self.move_id.line_ids:
            if line.account_id.user_type_id.type == "receivable":
                receivable_lines.append(line.id)
        self.l10n_br_receivable_move_line_ids = \
            self.env['account.move.line'].browse(list(set(receivable_lines)))

    @api.one
    @api.depends('move_id.line_ids')
    def _compute_payables(self):
        payable_lines = []
        for line in self.move_id.line_ids:
            if line.account_id.user_type_id.type == "payable":
                payable_lines.append(line.id)
        self.l10n_br_payable_move_line_ids = \
            self.env['account.move.line'].browse(list(set(payable_lines)))

    l10n_br_total_tax = fields.Float(
        string='Impostos ( + )', readonly=True, compute='_compute_amount',
        digits=dp.get_precision('Account'), store=True, oldname='total_tax')

    l10n_br_receivable_move_line_ids = fields.Many2many(
        'account.move.line', string='Receivable Move Lines',
        compute='_compute_receivables', oldname='receivable_move_line_ids')

    l10n_br_payable_move_line_ids = fields.Many2many(
        'account.move.line', string='Payable Move Lines',
        compute='_compute_payables', oldname='payable_move_line_ids')

    l10n_br_product_serie_id = fields.Many2one(
        'br_account.document.serie', string=u'Série produtos',
        domain="[('fiscal_document_id', '=', l10n_br_product_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]}, oldname='product_serie_id')
    l10n_br_product_document_id = fields.Many2one(
        'br_account.fiscal.document', string='Documento produtos',
        readonly=True, states={'draft': [('readonly', False)]},
        oldname='product_document_id')
    l10n_br_service_serie_id = fields.Many2one(
        'br_account.document.serie', string=u'Série serviços',
        domain="[('fiscal_document_id', '=', l10n_br_service_document_id),\
        ('company_id','=',company_id)]", readonly=True,
        states={'draft': [('readonly', False)]}, oldname='service_serie_id')
    l10n_br_service_document_id = fields.Many2one(
        'br_account.fiscal.document', string='Documento serviços',
        readonly=True, states={'draft': [('readonly', False)]},
        oldname='service_document_id')
    l10n_br_fiscal_document_related_ids = fields.One2many(
        'br_account.document.related', 'invoice_id',
        'Documento Fiscal Relacionado', readonly=True,
        states={'draft': [('readonly', False)]},
        oldname='fiscal_document_related_ids')
    l10n_br_fiscal_observation_ids = fields.Many2many(
        'br_account.fiscal.observation', string=u"Observações Fiscais",
        readonly=True, states={'draft': [('readonly', False)]},
        oldname='fiscal_observation_ids')
    l10n_br_fiscal_comment = fields.Text(
        u'Observação Fiscal', readonly=True,
        states={'draft': [('readonly', False)]},
        oldname='fiscal_comment')

    l10n_br_total_bruto = fields.Float(
        string='Total Bruto ( = )', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='total_bruto')
    l10n_br_total_desconto = fields.Float(
        string='Desconto ( - )', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='total_desconto')

    l10n_br_icms_base = fields.Float(
        string='Base ICMS', store=True, compute='_compute_amount',
        digits=dp.get_precision('Account'), oldname='icms_base')
    l10n_br_icms_value = fields.Float(
        string='Valor ICMS', digits=dp.get_precision('Account'),
        compute='_compute_amount', store=True, oldname='icsm_value')
    l10n_br_icms_st_base = fields.Float(
        string='Base ICMS ST', store=True, compute='_compute_amount',
        digits=dp.get_precision('Account'), oldname='icsm_st_base')
    l10n_br_icms_st_value = fields.Float(
        string='Valor ICMS ST', store=True, compute='_compute_amount',
        digits=dp.get_precision('Account'), oldname='icms_st_value')
    l10n_br_valor_icms_fcp_uf_dest = fields.Float(
        string="Total ICMS FCP", store=True, compute='_compute_amount',
        help=u'Total total do ICMS relativo Fundo de Combate à Pobreza (FCP) \
        da UF de destino', oldname='valor_icms_fcp_uf_dest')
    l10n_br_valor_icms_uf_dest = fields.Float(
        string="ICMS Destino", store=True, compute='_compute_amount',
        help='Valor total do ICMS Interestadual para a UF de destino',
        oldname='valor_icms_uf_dest')
    l10n_br_valor_icms_uf_remet = fields.Float(
        string="ICMS Remetente", store=True, compute='_compute_amount',
        help='Valor total do ICMS Interestadual para a UF do Remetente',
        oldname='valor_icms_uf_remet')
    l10n_br_issqn_base = fields.Float(
        string='Base ISSQN', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='issqn_base')
    l10n_br_issqn_value = fields.Float(
        string='Valor ISSQN', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='issqn_value')
    l10n_br_issqn_retention = fields.Float(
        string='ISSQN Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='issqn_retention')
    l10n_br_ipi_base = fields.Float(
        string='Base IPI', store=True, digits=dp.get_precision('Account'),
        compute='_compute_amount', oldname='ipi_base')
    l10n_br_ipi_base_other = fields.Float(
        string="Base IPI Outras", store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='ipi_base_other')
    l10n_br_ipi_value = fields.Float(
        string='Valor IPI', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='ipi_value')
    l10n_br_pis_base = fields.Float(
        string='Base PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='pis_base')
    l10n_br_pis_value = fields.Float(
        string='Valor PIS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='pis_value')
    l10n_br_pis_retention = fields.Float(
        string='PIS Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='pis_retention')
    l10n_br_cofins_base = fields.Float(
        string='Base COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='cofins_base')
    l10n_br_cofins_value = fields.Float(
        string='Valor COFINS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True, oldname='confis_value')
    l10n_br_cofins_retention = fields.Float(
        string='COFINS Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        readonly=True, oldname='cofins_retention')
    l10n_br_ii_base = fields.Float(
        string='Base II', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='ii_base')
    l10n_br_ii_value = fields.Float(
        string='Valor II', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='ii_value')
    l10n_br_csll_base = fields.Float(
        string='Base CSLL', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='csll_base')
    l10n_br_csll_value = fields.Float(
        string='Valor CSLL', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='csll_value')
    l10n_br_csll_retention = fields.Float(
        string='CSLL Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='csll_retention')
    l10n_br_irrf_base = fields.Float(
        string='Base IRRF', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='irrf_base')
    l10n_br_irrf_value = fields.Float(
        string='Valor IRRF', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='irrf_value')
    l10n_br_irrf_retention = fields.Float(
        string='IRRF Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='irrf_retention')
    l10n_br_inss_base = fields.Float(
        string='Base INSS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='inss_base')
    l10n_br_inss_value = fields.Float(
        string='Valor INSS', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='inss_value')
    l10n_br_inss_retention = fields.Float(
        string='INSS Retido', store=True,
        digits=dp.get_precision('Account'), compute='_compute_amount',
        oldname='inss_retention')
    l10n_br_total_tributos_federais = fields.Float(
        string='Total de Tributos Federais',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        oldname='total_tributos_federais')
    l10n_br_total_tributos_estaduais = fields.Float(
        string='Total de Tributos Estaduais',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        oldname='total_tributos_estaduais')
    l10n_br_total_tributos_municipais = fields.Float(
        string='Total de Tributos Municipais',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        oldname='total_tributos_municipais')
    l10n_br_total_tributos_estimados = fields.Float(
        string='Total de Tributos',
        store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_amount',
        oldname='total_tributos_estimados')

    @api.onchange('fiscal_position_id')
    def _onchange_br_account_fiscal_position_id(self):
        if (self.fiscal_position_id
                and self.fiscal_position_id.l10n_br_account_id):
            self.account_id = self.fiscal_position_id.l10n_br_account_id.id
        if (self.fiscal_position_id and
                self.fiscal_position_id.l10n_br_journal_id):
            self.journal_id = self.fiscal_position_id.l10n_br_journal_id

        self.l10n_br_product_serie_id = \
            self.fiscal_position_id.l10n_br_product_serie_id.id
        self.l10n_br_product_document_id = \
            self.fiscal_position_id.l10n_br_product_document_id.id

        self.l10n_br_service_serie_id = \
            self.fiscal_position_id.l10n_br_service_serie_id.id
        self.l10n_br_service_document_id = \
            self.fiscal_position_id.l10n_br_service_document_id.id

        ob_ids = [x.id for x in
                  self.fiscal_position_id.l10n_br_fiscal_observation_ids]
        self.l10n_br_fiscal_observation_ids = [(6, False, ob_ids)]

    @api.multi
    def action_invoice_cancel_paid(self):
        if self.filtered(lambda inv: inv.state not in ['proforma2', 'draft',
                                                       'open', 'paid']):
            raise UserError(_("Invoice must be in draft, Pro-forma or open \
                              state in order to be cancelled."))
        return self.action_cancel()

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        contador = 0

        for line in self.invoice_line_ids.filtered(
                lambda x: x.l10n_br_localization):
            if line.quantity == 0:
                continue
            res[contador]['price'] = line.price_total

            price = line.price_unit * (1 - (
                line.discount or 0.0) / 100.0)

            ctx = line._prepare_tax_context()
            tax_ids = line.invoice_line_tax_ids.with_context(**ctx)

            taxes_dict = tax_ids.compute_all(
                price, self.currency_id, line.quantity,
                product=line.product_id, partner=self.partner_id)
            for tax in line.invoice_line_tax_ids:
                tax_dict = next(
                    x for x in taxes_dict['taxes'] if x['id'] == tax.id)
                if not tax.price_include and tax.account_id:
                    res[contador]['price'] += tax_dict['amount']
                if tax.price_include and (not tax.account_id or
                                          not tax.l10n_br_deduced_account_id):
                    if tax_dict['amount'] > 0.0:  # Negativo é retido
                        res[contador]['price'] -= tax_dict['amount']

            contador += 1

        return res

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        res = super(AccountInvoice, self).\
            finalize_invoice_move_lines(move_lines)
        if not self.l10n_br_localization:
            return res
        count = 1
        for invoice_line in res:
            line = invoice_line[2]
            line['ref'] = self.origin
            if line['name'] == '/' or (
               line['name'] == self.name and self.name):
                line['name'] = "%02d" % count
                count += 1
        return res

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            other_taxes = line.invoice_line_tax_ids.filtered(
                lambda x: not x.l10n_br_domain)
            line.invoice_line_tax_ids = \
                other_taxes | line.l10n_br_tax_icms_id | \
                line.l10n_br_tax_ipi_id | line.l10n_br_tax_pis_id | \
                line.l10n_br_tax_cofins_id | line.l10n_br_tax_issqn_id | \
                line.l10n_br_tax_ii_id | line.l10n_br_tax_icms_st_id | \
                line.l10n_br_tax_csll_id | line.l10n_br_tax_irrf_id | \
                line.l10n_br_tax_inss_id

            ctx = line._prepare_tax_context()
            tax_ids = line.invoice_line_tax_ids.with_context(**ctx)

            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_ids.compute_all(
                price_unit, self.currency_id, line.quantity,
                line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(
                    tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += round(val['amount'], 2)
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.model
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()
        if not self.l10n_br_localization:
            return res
        done_taxes = []
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount and tax_line.tax_id.l10n_br_deduced_account_id:
                tax = tax_line.tax_id
                done_taxes.append(tax.id)
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount * -1,
                    'quantity': 1,
                    'price': tax_line.amount * -1,
                    'account_id': (tax_line.tax_id.
                                   l10n_br_deduced_account_id.id),
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'invoice_id': self.id,
                    'tax_ids': [(6, 0, done_taxes)]
                    if tax_line.tax_id.include_base_amount else []
                })
        return res

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        if not self.l10n_br_localization:
            return res
        res['l10n_br_product_document_id'] = \
            invoice.l10n_br_product_document_id.id
        res['l10n_br_product_serie_id'] = invoice.l10n_br_product_serie_id.id
        res['l10n_br_service_document_id'] = \
            invoice.l10n_br_service_document_id.id
        res['l10n_br_service_serie_id'] = invoice.l10n_br_service_serie_id.id
        return res
