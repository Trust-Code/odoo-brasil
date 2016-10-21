# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    @api.multi
    def _load_template(self, company, code_digits=None,
                       transfer_account_id=None, account_ref=None,
                       taxes_ref=None):
        acc_ref, tax_ref = super(AccountChartTemplate, self)._load_template(
            company, code_digits, transfer_account_id, account_ref, taxes_ref)

        tax_tmpl_obj = self.env['account.tax.template']
        tax_obj = self.env['account.tax']
        for key, value in tax_ref.items():
            tax_tmpl_id = tax_tmpl_obj.browse(key)
            tax_obj.browse(value).write({
                'deduced_account_id': acc_ref.get(
                    tax_tmpl_id.deduced_account_id.id, False),
                'refund_deduced_account_id': acc_ref.get(
                    tax_tmpl_id.refund_deduced_account_id.id, False)
            })
        return acc_ref, tax_ref


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    deduced_account_id = fields.Many2one(
        'account.account.template', string="Conta de Dedução da Venda")
    refund_deduced_account_id = fields.Many2one(
        'account.account.template', string="Conta de Dedução do Reembolso")
    domain = fields.Selection([('icms', 'ICMS'),
                               ('icmsst', 'ICMS ST'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('outros', 'Outros')], string="Tipo")
    amount_type = fields.Selection(selection_add=[('icmsst', 'ICMS ST')])

    def _get_tax_vals(self, company):
        res = super(AccountTaxTemplate, self)._get_tax_vals(company)
        res['domain'] = self.domain
        res['amount_type'] = self.amount_type
        return res


class AccountTax(models.Model):
    _inherit = 'account.tax'

    deduced_account_id = fields.Many2one(
        'account.account', string="Conta de Dedução da Venda")
    refund_deduced_account_id = fields.Many2one(
        'account.account', string="Conta de Dedução do Reembolso")
    domain = fields.Selection([('icms', 'ICMS'),
                               ('icmsst', 'ICMS ST'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('outros', 'Outros')], string="Tipo")
    amount_type = fields.Selection(selection_add=[('icmsst', 'ICMS ST')])

    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0,
                    product=None, partner=None):

        exists_br_tax = len(self.filtered(lambda x: x.domain)) > 0

        icms_taxes = self.filtered(lambda x: x.domain in ('icms', 'icmsst'))
        self = self - icms_taxes
        res = super(AccountTax, self).compute_all(
            price_unit, currency, quantity, product, partner)
        if not exists_br_tax:
            res['price_without_tax'] = round(price_unit * quantity, 2)
            return res

        incluir_ipi = False
        aliquota_mva = 0.0
        if 'incluir_ipi_base' in self.env.context:
            incluir_ipi = self.env.context['incluir_ipi_base']
        if 'aliquota_mva' in self.env.context:
            aliquota_mva = self.env.context['aliquota_mva']

        ipi = self.filtered(lambda x: x.domain == 'ipi')
        total_ipi = sum(x['amount'] for x in res['taxes'] if x['id'] == ipi.id)

        base = round(price_unit * quantity, 2)
        icms_amount = 0.0
        icmsst_amount = 0.0

        if incluir_ipi:
            base += total_ipi
        icms = icms_taxes.filtered(lambda x: x.domain == 'icms')
        if icms:
            icms_amount = icms._compute_amount(
                base, price_unit, quantity, product, partner)

        icmsst = icms_taxes.filtered(lambda x: x.domain == 'icmsst')
        if icms and icmsst:
            base_icms_proprio = round(price_unit * quantity, 2)
            icms_proprio = base_icms_proprio * icms.amount / 100
            base_st = base * (1 + aliquota_mva / 100)
            icmsst = icmsst.with_context({'icms_proprio': icms_proprio})
            icmsst_amount = icmsst._compute_amount(
                base_st, price_unit, quantity, product, partner)

        for tax in icms_taxes:
            amount = 0
            base = 0
            if tax.domain == 'icms':
                base = base
                amount = icms_amount
            if tax.domain == 'icmsst':
                base = base_st
                amount = icmsst_amount
            if amount > 0.0:
                res['taxes'].append({
                    'id': tax.id,
                    'name': tax.with_context(
                        **{'lang': partner.lang} if partner else {}).name,
                    'base': base,
                    'amount': amount,
                    'sequence': tax.sequence,
                    'account_id': tax.account_id.id,
                    'refund_account_id': tax.refund_account_id.id,
                    'analytic': tax.analytic,
                })

        # Restore self
        self = self | icms_taxes
        total_excluded = total_included = round(price_unit * quantity, 2)

        for tax in res['taxes']:
            tax_id = self.filtered(lambda x: x.id == tax['id'])
            if not tax_id.price_include:
                total_included += tax['amount']

        res['total_included'] = total_included
        res['price_without_tax'] = total_excluded
        return res

    def _compute_amount(self, base_amount, price_unit, quantity=1.0,
                        product=None, partner=None):

        if self.amount_type == 'icmsst':
            icms_proprio = self.env.context['icms_proprio']
            return (base_amount * self.amount / 100) - icms_proprio
        return super(AccountTax, self)._compute_amount(
            base_amount, price_unit, quantity, product, partner)
