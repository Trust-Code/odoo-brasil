# © 2021 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    def _get_tax_vals(self, company, tax_template_to_tax):
        res = super(AccountTaxTemplate, self)._get_tax_vals(
            company, tax_template_to_tax)
        res['domain'] = self.domain
        res['amount_type'] = self.amount_type
        return res


class AccountTax(models.Model):
    _inherit = 'account.tax'

    difal_por_dentro = fields.Boolean(string="Calcular Difal por Dentro?")
    icms_st_incluso = fields.Boolean(string="Incluir ICMS ST na Base de Calculo?")

    @api.onchange('domain')
    def _onchange_domain_tax(self):
        if self.domain in ('icms', 'pis', 'cofins', 'iss', 'ii',
                           'icms_inter', 'icms_intra', 'fcp'):
            self.price_include = True
            self.amount_type = 'division'
        if self.domain in ('icmsst', 'ipi', 'fcpst'):
            self.price_include = False
            self.include_base_amount = False
            self.amount_type = 'percent'

    @api.onchange('deduced_account_id')
    def _onchange_deduced_account_id(self):
        self.refund_deduced_account_id = self.deduced_account_id

    def _tax_vals(self, tax):
        tax_repartition_lines = tax.invoice_repartition_line_ids.filtered(lambda x: x.repartition_type == 'tax')
        return {
            'id': tax.id,
            'name': tax.name,
            'sequence': tax.sequence,
            'account_id': tax_repartition_lines[0].account_id.id,
            'tax_repartition_line_id': tax_repartition_lines[0].id,
            'analytic': tax.analytic,
            'tag_ids': [],
            'tax_ids': [],
            'domain': tax.domain,
            'aliquota': tax.amount,
            'tax_exigibility': tax.tax_exigibility,
            'price_include': tax.price_include
        }

    def l10n_br_compute_amount_tax(self, base_amount, sign):
        # TODO Usar o tax_repartition_lines posteriormente, nao vejo utilidade para isso.
        # tax_repartition_lines = (is_refund and self.refund_repartition_line_ids or self.invoice_repartition_line_ids).filtered(lambda x: x.repartition_type == 'tax')

        self.ensure_one()

        amount = 0
        if (self.amount_type == 'percent' and not self.price_include) or (self.amount_type == 'division' and self.price_include):
            amount = base_amount * self.amount / 100
        if self.amount_type == 'percent' and self.price_include:
            amount = base_amount - (base_amount / (1 + self.amount / 100))
        if self.amount_type == 'division' and not self.price_include:
            amount = base_amount / (1 - self.amount / 100) - base_amount
        return round(amount * sign, 2)

    def _compute_ipi(self, price_base, sign):
        ipi_tax = self.filtered(lambda x: x.domain == 'ipi')
        if not ipi_tax:
            return []
        vals = self._tax_vals(ipi_tax)
        base_tax = self.calc_ipi_base(price_base, sign)

        if 'ipi_base_calculo_manual' in self.env.context and\
                self.env.context['ipi_base_calculo_manual'] > 0:
            vals['base'] = self.env.context['ipi_base_calculo_manual']
        else:
            vals['base'] = base_tax
        vals['amount'] = ipi_tax.l10n_br_compute_amount_tax(vals['base'], sign)
        return [vals]

    def calc_ipi_base(self, price_base, sign):
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

        return base_ipi * (1 - (reducao_ipi / 100.0))

    def _compute_icms(self, price_base, ipi_value, sign):
        icms_tax = self.filtered(lambda x: x.domain == 'icms')
        if not icms_tax:
            return []
        result = []
        for tax in icms_tax:
            vals = self._tax_vals(tax)
            base_diferida = base_icms = tax.calc_icms_base(price_base, ipi_value)
            if "icms_aliquota_diferimento" in self.env.context:
                diferimento_icms = self.env.context['icms_aliquota_diferimento']
                base_diferida = base_icms * (1 - (diferimento_icms / 100.0))
            vals['amount'] = tax.l10n_br_compute_amount_tax(base_diferida, sign)
            vals['base'] = base_icms
            result += [vals]
        return result

    def calc_icms_base(self, price_base, ipi_value):
        base_icms = price_base
        incluir_ipi = False
        reducao_icms = 0.0
        if 'incluir_ipi_base' in self.env.context:
            incluir_ipi = self.env.context['incluir_ipi_base']
        if "icms_aliquota_reducao_base" in self.env.context:
            reducao_icms = self.env.context['icms_aliquota_reducao_base']

        if incluir_ipi:
            base_icms += abs(ipi_value)
        if "valor_frete" in self.env.context:
            base_icms += self.env.context["valor_frete"]
        if "valor_seguro" in self.env.context:
            base_icms += self.env.context["valor_seguro"]
        if "outras_despesas" in self.env.context:
            base_icms += self.env.context["outras_despesas"]

        return base_icms * (1 - (reducao_icms / 100.0))

    def _compute_icms_st(self, price_base, ipi_value, icms_value, sign):
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
            base_icmsst = self.env.context['icms_st_base_calculo_manual']
        if icmsst_tax.icms_st_incluso:
            icmsst = round(
                ((base_icmsst - icms_value)*(icmsst_tax.amount / 100.0) / (
                    1 - icmsst_tax.amount / 100.0)) - icms_value, 2)
        else:
            icmsst = round(
                (base_icmsst * (icmsst_tax.amount / 100.0)) - icms_value, 2)
        vals['amount'] = icmsst * sign if icmsst >= 0.0 else 0.0
        vals['base'] = base_icmsst

        taxes = [vals]

        fcpst_tax = self.filtered(lambda x: x.domain == 'fcpst')
        if fcpst_tax:
            fcpst_vals = self._tax_vals(fcpst_tax)
            fcpst_vals['amount'] = fcpst_tax.l10n_br_compute_amount_tax(base_icmsst, sign)
            fcpst_vals['base'] = base_icmsst
            taxes.append(fcpst_vals)
        return taxes

    def _compute_difal(self, price_base, ipi_value, sign):
        icms_inter = self.filtered(lambda x: x.domain == 'icms_inter')
        icms_intra = self.filtered(lambda x: x.domain == 'icms_intra')
        icms_fcp = self.filtered(lambda x: x.domain == 'fcp')

        taxes = []
        base_icms = price_base + ipi_value
        for tax_inter in icms_inter:
            vals_inter = self._tax_vals(tax_inter)

            if tax_inter.amount > 0:
                tax_intra = icms_intra.filtered(lambda x: x.amount > 0)
                # sign = 1
            else:
                tax_intra = icms_intra.filtered(lambda x: x.amount < 0)
                # sign = -1

            vals_intra = self._tax_vals(tax_intra)

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
            interestadual = tax_inter.l10n_br_compute_amount_tax(base_icms, 1.0)
            vals_inter['base'] = base_icms
            vals_intra['base'] = base_icms

            if tax_inter.difal_por_dentro or tax_intra.difal_por_dentro:
                base_icms = base_icms - interestadual
                base_icms = base_icms / (1 - (tax_intra.amount) / 100)

            interno = tax_intra.l10n_br_compute_amount_tax(base_icms, 1.0)

            if 'icms_aliquota_inter_part' in self.env.context:
                icms_inter_part = self.env.context["icms_aliquota_inter_part"]
            else:
                icms_inter_part = 100.0
            vals_inter['amount'] = round((interno - interestadual) * sign *
                                        (100 - icms_inter_part) / 100, 2)
            vals_intra['amount'] = round((interno - interestadual) * sign *
                                        icms_inter_part / 100, 2)

            taxes += [vals_inter, vals_intra]

        for tax in icms_fcp:
            vals_fcp = self._tax_vals(tax)
            fcp = tax.l10n_br_compute_amount_tax(base_icms, 1.0)
            vals_fcp['amount'] = fcp
            vals_fcp['base'] = base_icms
            taxes += [vals_fcp]
        return taxes

    def _compute_pis_cofins(self, price_base, sign):
        pis_cofins_tax = self.filtered(lambda x: x.domain in ('pis', 'cofins'))
        if not pis_cofins_tax:
            return []
        taxes = []
        for tax in pis_cofins_tax:
            vals = self._tax_vals(tax)
            if tax.domain == 'pis':
                if 'pis_base_calculo_manual' in self.env.context and\
                        self.env.context['pis_base_calculo_manual'] > 0:
                    vals['amount'] = tax.l10n_br_compute_amount_tax(
                        self.env.context['pis_base_calculo_manual'], 1.0)
                    vals['base'] = self.env.context['pis_base_calculo_manual']
                else:
                    vals['amount'] = tax.l10n_br_compute_amount_tax(price_base, sign)
                    vals['base'] = price_base
            if tax.domain == 'cofins':
                if 'cofins_base_calculo_manual' in self.env.context and\
                        self.env.context['cofins_base_calculo_manual'] > 0:
                    vals['amount'] = tax.l10n_br_compute_amount_tax(
                        self.env.context['cofins_base_calculo_manual'], 1.0)
                    vals['base'] = self.env.context[
                        'cofins_base_calculo_manual']
                else:
                    vals['amount'] = tax.l10n_br_compute_amount_tax(price_base, sign)
                    vals['base'] = price_base
            vals['amount'] = round(vals['amount'], 2)
            taxes.append(vals)
        return taxes

    def _compute_ii(self, price_base, sign):
        ii_tax = self.filtered(lambda x: x.domain == 'ii')
        if not ii_tax:
            return []
        if "ii_base_calculo" in self.env.context and \
                self.env.context['ii_base_calculo'] > 0:
            price_base = self.env.context["ii_base_calculo"]
        taxes = []
        for tax in ii_tax:
            vals = self._tax_vals(tax)
            vals['amount'] = tax.l10n_br_compute_amount_tax(price_base, sign)
            vals['base'] = price_base
            taxes.append(vals)
        return taxes

    def _compute_issqn(self, price_base, sign):
        issqn_tax = self.filtered(lambda x: x.domain == 'iss')
        if not issqn_tax:
            return []
        issqn_deduction = self.env.context.get('l10n_br_issqn_deduction', 0.0)
        price_base *= (1 - (issqn_deduction / 100.0))
        taxes = []
        for tax in issqn_tax:
            vals = self._tax_vals(tax)
            vals['amount'] = tax.l10n_br_compute_amount_tax(price_base, sign)
            vals['base'] = price_base
            taxes.append(vals)
        return taxes

    def _compute_retention(self, price_base, sign):
        retention_tax = self.filtered(
            lambda x: x.domain in ('csll', 'irrf', 'inss'))
        if not retention_tax:
            return []
        taxes = []
        for tax in retention_tax:
            vals = self._tax_vals(tax)
            vals['amount'] = tax.l10n_br_compute_amount_tax(price_base, sign)
            vals['base'] = price_base
            taxes.append(vals)
        return taxes

    def _compute_others(self, price_base, sign):
        others = self.filtered(lambda x: x.domain == 'outros' or not x.domain)
        if not others:
            return []
        result = []
        for tax in others:
            vals = self._tax_vals(tax)
            vals['amount'] = tax.l10n_br_compute_amount_tax(price_base, sign)
            vals['base'] = price_base
            result += [vals]
        return result

    def sum_taxes(self, price_base, sign):
        ipi = self._compute_ipi(price_base, sign)
        icms = self._compute_icms(
            price_base,
            ipi[0]['amount'] if ipi else 0.0, sign)
        icmsst = self._compute_icms_st(
            price_base,
            ipi[0]['amount'] if ipi else 0.0,
            icms[0]['amount'] if icms else 0.0, sign)

        difal = self._compute_difal(
            price_base, ipi[0]['amount'] if ipi else 0.0, sign)

        taxes = icms + icmsst + difal + ipi
        taxes += self._compute_pis_cofins(price_base, sign)
        taxes += self._compute_issqn(price_base, sign)
        taxes += self._compute_ii(price_base, sign)
        taxes += self._compute_retention(price_base, sign)
        taxes += self._compute_others(price_base, sign)
        return taxes

    def compute_all(
        self,
        price_unit,
        currency=None,
        quantity=1.0,
        product=None,
        partner=None,
        is_refund=False,
        handle_price_include=True,
        include_caba_tags=False,
    ):
        """
        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'total_void'    : 0.0,    # Total with those taxes, that don't have an account set
            'taxes': [{               # One dict for each tax in self and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }],
        }
        """
        # 1) Flatten the taxes before to get grouped taxes with domain
        taxes, groups_map = self.flatten_taxes_hierarchy(create_map=True)

        exists_br_tax = len(taxes.filtered(lambda x: x.domain)) > 0
        if not exists_br_tax:
            res = super(AccountTax, self).compute_all(
                price_unit,
                currency,
                quantity,
                product,
                partner,
                is_refund,
                handle_price_include,
                include_caba_tags,
            )
            return res

        if not self:
            company = self.env.company
        else:
            company = self[0].company_id

        # 2) Deal with the rounding methods
        if not currency:
            currency = company.currency_id

        base = currency.round(price_unit * quantity)

        # 3) Get the sign
        sign = 1
        if currency.is_zero(base):
            sign = self._context.get('force_sign', 1)
        elif base < 0:
            sign = -1
        if base < 0:
            base = -base

        taxes_vals = taxes.with_context(handle_price_include=handle_price_include).sum_taxes(base, sign)
        total_included = total_excluded = total_void = base
        for tax in taxes_vals:
            price_include = self._context.get('force_price_include', tax.get("price_include"))
            if price_include:
                total_excluded -= sign * round(tax['amount'], 2)
            total_void -= sign * round(tax['amount'], 2)
            tax.update({
                'group': groups_map.get(
                    taxes.filtered(lambda x: x.id == tax.get("id"))
                ),
            })

        vals = {
            'base_tags': taxes.mapped(is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids').filtered(lambda x: x.repartition_type == 'base').mapped('tag_ids').ids,
            'taxes': taxes_vals,
            'total_excluded': sign * total_excluded,
            'total_included': sign * currency.round(total_included),
            'total_void': sign * currency.round(total_void),
            'price_without_tax': sign * total_included,
        }
        return vals
