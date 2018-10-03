# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        super(PurchaseOrder, self)._amount_all()
        for order in self:
            order.update({
                'amount_total': order.total_bruto + order.total_tax +
                order.total_frete + order.total_seguro +
                order.total_despesas - order.total_desconto,
            })
        self._onchange_despesas_frete_seguro()

    def _calc_ratio(self, qty, total):
        if total > 0:
            return qty / total
        else:
            return 0

    def calc_rateio(self, line, total):
        porcentagem = self._calc_ratio(line.valor_bruto, total)
        frete = self.total_frete * porcentagem
        seguro = self.total_seguro * porcentagem
        despesas = self.total_despesas * porcentagem
        aduana = self.total_despesas_aduana * porcentagem
        line.update({
            'valor_seguro': seguro,
            'valor_frete': frete,
            'outras_despesas': despesas,
            'valor_aduana': aduana
        })
        return frete, seguro, despesas, aduana

    def calc_total_amount(self):
        amount = 0
        for line in self.order_line:
            if line.product_id.fiscal_type == 'product':
                amount += line.valor_bruto
        return amount

    @api.onchange('total_despesas', 'total_seguro',
                  'total_frete', 'total_despesas_aduana')
    def _onchange_despesas_frete_seguro(self):
        amount = self.calc_total_amount()
        sub_frete = self.total_frete
        sub_seguro = self.total_seguro
        sub_aduana = self.total_despesas_aduana
        sub_desp = self.total_despesas
        for l in self.order_line:
            if l.product_id.fiscal_type == 'service':
                continue
            else:
                frete, seguro, despesas, aduana = self.calc_rateio(
                    l, amount)
                sub_frete -= round(frete, 2)
                sub_seguro -= round(seguro, 2)
                sub_aduana -= round(aduana, 2)
                sub_desp -= round(despesas, 2)
        if self.order_line:
            self.order_line[0].update({
                'valor_seguro':
                    self.order_line[0].valor_seguro + sub_seguro,
                'valor_frete':
                    self.order_line[0].valor_frete + sub_frete,
                'outras_despesas':
                    self.order_line[0].outras_despesas + sub_desp,
                'valor_aduana':
                    self.order_line[0].valor_aduana + sub_aduana
                })

    total_despesas = fields.Float(
        string='Despesas ( + )', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    total_despesas_aduana = fields.Float(
        string='Despesas Aduaneiras', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    total_seguro = fields.Float(
        string='Seguro ( + )', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    total_frete = fields.Float(
        string='Frete ( + )', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})


class PuchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    valor_seguro = fields.Float(
        'Seguro', default=0.0, digits=dp.get_precision('Account'))
    outras_despesas = fields.Float(
        'Despesas', default=0.0, digits=dp.get_precision('Account'))
    valor_frete = fields.Float(
        'Frete', default=0.0, digits=dp.get_precision('Account'))
    valor_aduana = fields.Float(
        default=0.0, digits=dp.get_precision('Account'))

    def _prepare_tax_context(self):
        res = super(PuchaseOrderLine, self)._prepare_tax_context()
        res.update({
            'valor_frete': self.valor_frete,
            'valor_seguro': self.valor_seguro,
            'outras_despesas': self.outras_despesas,
            'ii_despesas': self.valor_aduana,
            'fiscal_type': self.fiscal_position_type,
        })
        return res

    @api.multi
    def _get_stock_move_price_unit(self):
        price = super(PuchaseOrderLine, self)._get_stock_move_price_unit()
        price = price + \
            (self.valor_frete/self.product_qty) + \
            (self.valor_seguro/self.product_qty) + \
            (self.outras_despesas/self.product_qty)
        return price
