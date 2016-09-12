# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2012  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.addons.l10n_br_base.tools.misc import calc_price_ratio
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_ind_pres(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.default_ind_pres

    @api.one
    def _get_costs_value(self):
        """ Read the l10n_br specific functional fields. """
        freight = costs = insurance = 0.0
        for line in self.order_line:
            freight += line.freight_value
            insurance += line.insurance_value
            costs += line.other_costs_value
        self.amount_freight = freight
        self.amount_costs = costs
        self.amount_insurance = insurance

    @api.one
    def _set_amount_freight(self):
        for line in self.order_line:
            line.write({
                'freight_value': calc_price_ratio(
                    line.price_gross,
                    self.amount_freight,
                    line.order_id.amount_untaxed),
                })
        return True

    @api.one
    def _set_amount_insurance(self):
        for line in self.order_line:
            line.write({
                'insurance_value': calc_price_ratio(
                    line.price_gross,
                    self.amount_insurance,
                    line.order_id.amount_untaxed),
                })
        return True

    @api.one
    def _set_amount_costs(self):
        for line in self.order_line:
            line.write({
                'other_costs_value': calc_price_ratio(
                    line.price_gross,
                    self.amount_costs,
                    line.order_id.amount_untaxed),
                })
        return True

    copy_note = fields.Boolean(u'Copiar Observação no documentos fiscal')
    ind_pres = fields.Selection([
        ('0', u'Não se aplica'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('9', u'Operação não presencial, outros')], u'Tipo de operação',
        readonly=True, states={'draft': [('readonly', False)]},
        required=False,
        help=u'Indicador de presença do comprador no estabelecimento \
             comercial no momento da operação.', default=_default_ind_pres)
    amount_freight = fields.Float(
        compute=_get_costs_value, inverse=_set_amount_freight,
        string='Frete', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    amount_costs = fields.Float(
        compute=_get_costs_value, inverse=_set_amount_costs,
        string='Outros Custos', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    amount_insurance = fields.Float(
        compute=_get_costs_value, inverse=_set_amount_insurance,
        string='Seguro', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(
        string='Desconto (-)',
        digits=dp.get_precision('Account'), store=True,
        help="The discount amount.")
    discount_rate = fields.Float(
        'Desconto', readonly=True, states={'draft': [('readonly', False)]})

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for sale_order in self:
            for sale_line in sale_order.order_line:
                sale_line.discount = sale_order.discount_rate

    def _fiscal_comment(self):
        fp_comment = []
        fp_ids = []

        for line in self.order_line:
            if line.fiscal_position_id and \
                    line.fiscal_position_id.inv_copy_note and \
                    line.fiscal_position_id.note:
                if line.fiscal_position_id.id not in fp_ids:
                    fp_comment.append(line.fiscal_position_id.note)
                    fp_ids.append(line.fiscal_position_id.id)

        return fp_comment

    @api.multi
    def _prepare_invoice(self):
        result = super(SaleOrder, self)._prepare_invoice()
        comment = []
        if self.note and self.copy_note:
            comment.append(self.note)

        fiscal_comment = self._fiscal_comment()
        result['comment'] = " - ".join(comment)
        result['fiscal_comment'] = " - ".join(fiscal_comment)
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _calc_line_base_price(self):
        return self.price_unit * (1 - (self.discount or 0.0) / 100.0)

    def _calc_line_quantity(self):
        return self.product_uom_qty

    def _calc_price_gross(self, qty):
        return self.price_unit * qty

    @api.one
    @api.depends('price_unit', 'tax_id', 'discount', 'product_uom_qty')
    def _amount_line(self):
        price = self._calc_line_base_price()
        qty = self._calc_line_quantity()
        self.discount_value = self.order_id.pricelist_id.currency_id.round(
            self.price_gross - (price * qty))

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position',
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    insurance_value = fields.Float('Insurance',
                                   default=0.0,
                                   digits=dp.get_precision('Account'))
    other_costs_value = fields.Float('Other costs',
                                     default=0.0,
                                     digits=dp.get_precision('Account'))
    freight_value = fields.Float('Freight',
                                 default=0.0,
                                 digits=dp.get_precision('Account'))

    discount_value = fields.Float(compute='_amount_line',
                                  string='Vlr. Desc. (-)',
                                  digits=dp.get_precision('Sale Price'))
    price_gross = fields.Float(
        compute='_amount_line', string='Vlr. Bruto',
        digits=dp.get_precision('Sale Price'))

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)

        res['insurance_value'] = self.insurance_value
        res['other_costs_value'] = self.other_costs_value
        res['freight_value'] = self.freight_value
        icms = self.tax_id.filtered(lambda x: x.domain == 'icms')
        if len(icms) > 1:
            raise UserError(
                'Apenas um imposto com o domínio ICMS deve ser cadastrado')
        res['tax_icms_id'] = icms and icms.id or False

        return res
