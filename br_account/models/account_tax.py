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
        'account.account.template', string=u"Conta de Dedução da Venda")
    refund_deduced_account_id = fields.Many2one(
        'account.account.template', string=u"Conta de Dedução do Reembolso")
    domain = fields.Selection([('icms', 'ICMS'),
                               ('icmsst', 'ICMS ST'),
                               ('simples', 'Simples Nacional'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('icms_inter', u'Difal - Alíquota Inter'),
                               ('icms_intra', u'Difal - Alíquota Intra'),
                               ('fcp', 'FCP'),
                               ('csll', 'CSLL'),
                               ('irrf', 'IRRF'),
                               ('inss', 'INSS'),
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
        'account.account', string=u"Conta de Dedução da Venda")
    refund_deduced_account_id = fields.Many2one(
        'account.account', string=u"Conta de Dedução do Reembolso")
    domain = fields.Selection([('icms', 'ICMS'),
                               ('icmsst', 'ICMS ST'),
                               ('simples', 'Simples Nacional'),
                               ('pis', 'PIS'),
                               ('cofins', 'COFINS'),
                               ('ipi', 'IPI'),
                               ('issqn', 'ISSQN'),
                               ('ii', 'II'),
                               ('icms_inter', u'Difal - Alíquota Inter'),
                               ('icms_intra', u'Difal - Alíquota Intra'),
                               ('fcp', 'FCP'),
                               ('csll', 'CSLL'),
                               ('irrf', 'IRRF'),
                               ('inss', 'INSS'),
                               ('outros', 'Outros')], string="Tipo")
    amount_type = fields.Selection(selection_add=[('icmsst', 'ICMS ST')])

    @api.onchange('domain')
    def _onchange_domain_tax(self):
        if self.domain in ('icms', 'simples', 'pis', 'cofins', 'issqn', 'ii',
                           'icms_inter', 'icms_intra', 'fcp'):
            self.price_include = True
            self.amount_type = 'division'
        if self.domain in ('icmsst', 'ipi'):
            self.price_include = False
            self.include_base_amount = False
            self.amount_type = 'division'
        if self.domain == 'icmsst':
            self.amount_type = 'icmsst'

    @api.onchange('deduced_account_id')
    def _onchange_deduced_account_id(self):
        self.refund_deduced_account_id = self.deduced_account_id

    def _tax_vals(self, tax):
        return {
            'id': tax.id,
            'name': tax.name,
            'sequence': tax.sequence,
            'account_id': tax.account_id.id,
            'refund_account_id': tax.refund_account_id.id,
            'analytic': tax.analytic
        }

    def _compute_ipi(self, price_base):
        ipi_tax = self.filtered(lambda x: x.domain == 'ipi')
        if not ipi_tax:
            return []
        vals = self._tax_vals(ipi_tax)
        reducao_ipi = 0.0
        if "ipi_reducao_bc" in self.env.context:
            reducao_ipi = self.env.context['ipi_reducao_bc']

        base_ipi = price_base
        if "valor_frete" in self.env.context:
            base_ipi += self.env.context["valor_frete"]
        if "valor_seguro" in self.env.context:
            base_ipi += self.env.context["valor_seguro"]
        if "outras_despesas" in self.env.context:
            base_ipi += self.env.context["outras_despesas"]

        base_tax = base_ipi * (1 - (reducao_ipi / 100.0))
        vals['amount'] = ipi_tax._compute_amount(base_tax, 1.0)
        if 'ipi_base_calculo_manual' in self.env.context and\
                self.env.context['ipi_base_calculo_manual'] > 0:
            vals['base'] = self.env.context['ipi_base_calculo_manual']
        else:
            vals['base'] = base_tax
        return [vals]

    def _compute_icms(self, price_base, ipi_value):
        icms_tax = self.filtered(lambda x: x.domain == 'icms')
        if not icms_tax:
            return []
        vals = self._tax_vals(icms_tax)
        base_icms = price_base
        incluir_ipi = False
        reducao_icms = 0.0
        if 'incluir_ipi_base' in self.env.context:
            incluir_ipi = self.env.context['incluir_ipi_base']
        if "icms_aliquota_reducao_base" in self.env.context:
            reducao_icms = self.env.context['icms_aliquota_reducao_base']

        if incluir_ipi:
            base_icms += ipi_value
        if "valor_frete" in self.env.context:
            base_icms += self.env.context["valor_frete"]
        if "valor_seguro" in self.env.context:
            base_icms += self.env.context["valor_seguro"]
        if "outras_despesas" in self.env.context:
            base_icms += self.env.context["outras_despesas"]

        base_icms *= 1 - (reducao_icms / 100.0)

        if 'icms_base_calculo_manual' in self.env.context and\
                self.env.context['icms_base_calculo_manual'] > 0:
            vals['amount'] = icms_tax._compute_amount(
                self.env.context['icms_base_calculo_manual'], 1.0)
            vals['base'] = self.env.context['icms_base_calculo_manual']
        else:
            vals['amount'] = icms_tax._compute_amount(base_icms, 1.0)
            vals['base'] = base_icms
        return [vals]

    def _compute_icms_st(self, price_base, ipi_value, icms_value):
        icmsst_tax = self.filtered(lambda x: x.domain == 'icmsst')
        if not icmsst_tax:
            return []
        vals = self._tax_vals(icmsst_tax)

        base_icmsst = price_base + ipi_value
        reducao_icmsst = 0.0
        aliquota_mva = 0.0
        if "icms_st_aliquota_reducao_base" in self.env.context:
            reducao_icmsst = self.env.context['icms_st_aliquota_reducao_base']
        if "icms_st_aliquota_mva" in self.env.context:
            aliquota_mva = self.env.context['icms_st_aliquota_mva']
        if "valor_frete" in self.env.context:
            base_icmsst += self.env.context["valor_frete"]
        if "valor_seguro" in self.env.context:
            base_icmsst += self.env.context["valor_seguro"]
        if "outras_despesas" in self.env.context:
            base_icmsst += self.env.context["outras_despesas"]

        base_icmsst *= 1 - (reducao_icmsst / 100.0)  # Redução

        deducao_st_simples = 0.0
        if "icms_st_aliquota_deducao" in self.env.context:
            deducao_st_simples = self.env.context["icms_st_aliquota_deducao"]

        if deducao_st_simples:
            icms_value = base_icmsst * (deducao_st_simples / 100.0)

        base_icmsst *= 1 + aliquota_mva / 100.0  # Aplica MVA

        if 'icms_st_base_calculo_manual' in self.env.context and\
                self.env.context['icms_st_base_calculo_manual'] > 0:
            icmsst = round(
                (self.env.context['icms_st_base_calculo_manual'] *
                 (icmsst_tax.amount / 100.0)) - icms_value, 2)
            vals['amount'] = icmsst if icmsst >= 0.0 else 0.0
            vals['base'] = self.env.context['icms_st_base_calculo_manual']
        else:
            icmsst = round(
                (base_icmsst * (icmsst_tax.amount / 100.0)) - icms_value, 2)
            vals['amount'] = icmsst if icmsst >= 0.0 else 0.0
            vals['base'] = base_icmsst
        return [vals]

    def _compute_difal(self, price_base, ipi_value):
        icms_inter = self.filtered(lambda x: x.domain == 'icms_inter')
        icms_intra = self.filtered(lambda x: x.domain == 'icms_intra')
        icms_fcp = self.filtered(lambda x: x.domain == 'fcp')
        if not icms_inter or not icms_intra:
            return []
        vals_fcp = None
        vals_inter = self._tax_vals(icms_inter)
        vals_intra = self._tax_vals(icms_intra)
        if icms_fcp:
            vals_fcp = self._tax_vals(icms_fcp)
        base_icms = price_base + ipi_value
        reducao_icms = 0.0
        if "icms_aliquota_reducao_base" in self.env.context:
            reducao_icms = self.env.context['icms_aliquota_reducao_base']

        if "valor_frete" in self.env.context:
            base_icms += self.env.context["valor_frete"]
        if "valor_seguro" in self.env.context:
            base_icms += self.env.context["valor_seguro"]
        if "outras_despesas" in self.env.context:
            base_icms += self.env.context["outras_despesas"]

        base_icms *= 1 - (reducao_icms / 100.0)
        interestadual = icms_inter._compute_amount(base_icms, 1.0)
        interno = icms_intra._compute_amount(base_icms, 1.0)

        vals_inter['amount'] = round((interno - interestadual) * 0.4, 2)
        vals_inter['base'] = base_icms
        vals_intra['amount'] = round((interno - interestadual) * 0.6, 2)
        vals_intra['base'] = base_icms

        taxes = [vals_inter, vals_intra]
        if vals_fcp:
            fcp = icms_fcp._compute_amount(base_icms, 1.0)
            vals_fcp['amount'] = fcp
            vals_fcp['base'] = base_icms
            taxes += [vals_fcp]
        return taxes

    def _compute_simples(self, price_base):
        simples_tax = self.filtered(lambda x: x.domain == 'simples')
        if not simples_tax:
            return []
        taxes = []
        for tax in simples_tax:
            vals = self._tax_vals(tax)
            vals['amount'] = tax._compute_amount(price_base, 1.0)
            vals['base'] = price_base
            taxes.append(vals)
        return taxes

    def _compute_pis_cofins(self, price_base):
        pis_cofins_tax = self.filtered(lambda x: x.domain in ('pis', 'cofins'))
        if not pis_cofins_tax:
            return []
        taxes = []
        for tax in pis_cofins_tax:
            vals = self._tax_vals(tax)
            if tax.domain == 'pis':
                if 'pis_base_calculo_manual' in self.env.context and\
                        self.env.context['pis_base_calculo_manual'] > 0:
                    vals['amount'] = tax._compute_amount(
                        self.env.context['pis_base_calculo_manual'], 1.0)
                    vals['base'] = self.env.context['pis_base_calculo_manual']
                else:
                    vals['amount'] = tax._compute_amount(price_base, 1.0)
                    vals['base'] = price_base
            if tax.domain == 'cofins':
                if 'cofins_base_calculo_manual' in self.env.context and\
                        self.env.context['cofins_base_calculo_manual'] > 0:
                    vals['amount'] = tax._compute_amount(
                        self.env.context['cofins_base_calculo_manual'], 1.0)
                    vals['base'] = self.env.context[
                        'cofins_base_calculo_manual']
                else:
                    vals['amount'] = tax._compute_amount(price_base, 1.0)
                    vals['base'] = price_base
            taxes.append(vals)
        return taxes

    def _compute_ii(self, price_base):
        ii_tax = self.filtered(lambda x: x.domain == 'ii')
        if not ii_tax:
            return []
        vals = self._tax_vals(ii_tax)
        if "ii_base_calculo" in self.env.context:
            price_base = self.env.context["ii_base_calculo"]
        vals['amount'] = ii_tax._compute_amount(price_base, 1.0)
        vals['base'] = price_base
        return [vals]

    def _compute_issqn(self, price_base):
        issqn_tax = self.filtered(lambda x: x.domain == 'issqn')
        if not issqn_tax:
            return []
        vals = self._tax_vals(issqn_tax)
        vals['amount'] = issqn_tax._compute_amount(price_base, 1.0)
        vals['base'] = price_base
        return [vals]

    def _compute_retention(self, price_base):
        retention_tax = self.filtered(
            lambda x: x.domain in ('csll', 'irrf', 'inss'))
        if not retention_tax:
            return []
        taxes = []
        for tax in retention_tax:
            vals = self._tax_vals(tax)
            vals['amount'] = tax._compute_amount(price_base, 1.0)
            vals['base'] = price_base
            taxes.append(vals)
        return taxes

    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0,
                    product=None, partner=None):

        exists_br_tax = len(self.filtered(lambda x: x.domain)) > 0
        if not exists_br_tax:
            res = super(AccountTax, self).compute_all(
                price_unit, currency, quantity, product, partner)
            res['price_without_tax'] = round(price_unit * quantity, 2)
            return res

        price_base = price_unit * quantity
        ipi = self._compute_ipi(price_base)
        icms = self._compute_icms(
            price_base,
            ipi[0]['amount'] if ipi else 0.0)
        icmsst = self._compute_icms_st(
            price_base,
            ipi[0]['amount'] if ipi else 0.0,
            icms[0]['amount'] if icms else 0.0)
        difal = self._compute_difal(
            price_base, ipi[0]['amount'] if ipi else 0.0)

        taxes = icms + icmsst + difal + ipi
        taxes += self._compute_simples(price_base)
        taxes += self._compute_pis_cofins(price_base)
        taxes += self._compute_issqn(price_base)
        taxes += self._compute_ii(price_base)
        taxes += self._compute_retention(price_base)

        total_included = total_excluded = price_base
        for tax in taxes:
            tax_id = self.filtered(lambda x: x.id == tax['id'])
            if not tax_id.price_include:
                total_included += tax['amount']

        return {
            'taxes': sorted(taxes, key=lambda k: k['sequence']),
            'total_excluded': total_excluded,
            'total_included': total_included,
            'base': price_base,
        }
