# -*- coding: utf-8 -*-
# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def calc_ipi_base(self, price_base):
        if ('fiscal_type' in self.env.context) and (
                self.env.context['fiscal_type'] == 'import'):
            reducao_ipi = 0.0
            base_ipi = price_base
            if "valor_frete" in self.env.context:
                base_ipi += self.env.context["valor_frete"]
            if "valor_seguro" in self.env.context:
                base_ipi += self.env.context["valor_seguro"]
            ii = self._compute_ii(price_base)
            base_ipi += ii[0]['amount']

            if "ipi_reducao_bc" in self.env.context:
                reducao_ipi = self.env.context['ipi_reducao_bc']
            return base_ipi * (1 - (reducao_ipi / 100.0))
        else:
            return super(AccountTax, self).calc_ipi_base(price_base)

    def calc_icms_base(self, price_base, ipi_value):
        if ('fiscal_type' in self.env.context) and (
                self.env.context['fiscal_type'] == 'import'):
            icms_tax = self.filtered(lambda x: x.domain == 'icms')
            ii = self._compute_ii(price_base)
            pis_cofins = self._compute_pis_cofins(price_base)
            base_icms = price_base
            reducao_icms = 0.0
            if "valor_frete" in self.env.context:
                base_icms += self.env.context["valor_frete"]
            if "valor_seguro" in self.env.context:
                base_icms += self.env.context["valor_seguro"]
            if "icms_aliquota_reducao_base" in self.env.context:
                reducao_icms = self.env.context['icms_aliquota_reducao_base']
            base_icms += ii[0]['amount']
            base_icms += ipi_value
            base_icms += sum([tax['amount'] for tax in pis_cofins])
            base_icms += self.env.context["ii_despesas"]
            base_icms = base_icms / (1 - icms_tax.amount/100)
            return base_icms * (1 - (reducao_icms / 100.0))
        else:
            return super(
                AccountTax, self).calc_icms_base(price_base, ipi_value)

    def _compute_pis_cofins(self, price_base):
        if ('fiscal_type' in self.env.context) and (
                self.env.context['fiscal_type'] == 'import'):
            if "valor_frete" in self.env.context:
                price_base += self.env.context["valor_frete"]
            if "valor_seguro" in self.env.context:
                price_base += self.env.context["valor_seguro"]
        return super(AccountTax, self)._compute_pis_cofins(price_base)

    def _compute_ii(self, price_base):
        if ('fiscal_type' in self.env.context) and (
                self.env.context['fiscal_type'] == 'import'):
            if "valor_frete" in self.env.context:
                price_base += self.env.context["valor_frete"]
            if "valor_seguro" in self.env.context:
                price_base += self.env.context["valor_seguro"]
        return super(AccountTax, self)._compute_ii(price_base)
