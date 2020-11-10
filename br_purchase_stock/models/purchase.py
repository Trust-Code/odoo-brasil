# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'br.localization.filtering']

    @api.depends('order_line.price_total')
    def _amount_all(self):
        super(PurchaseOrder, self)._amount_all()
        for order in self:
            order.update({
                'amount_total': (
                        order.l10n_br_total_bruto +
                        order.l10n_br_total_tax +
                        order.l10n_br_total_frete +
                        order.l10n_br_total_seguro +
                        order.l10n_br_total_despesas -
                        order.l10n_br_total_desconto),
            })
        self._onchange_despesas_frete_seguro()

    def _calc_ratio(self, qty, total):
        if total > 0:
            return qty / total
        else:
            return 0

    def calc_rateio(self, line, total):
        porcentagem = self._calc_ratio(line.l10n_br_valor_bruto, total)
        frete = self.l10n_br_total_frete * porcentagem
        seguro = self.l10n_br_total_seguro * porcentagem
        despesas = self.l10n_br_total_despesas * porcentagem
        aduana = self.l10n_br_total_despesas_aduana * porcentagem
        line.update({
            'l10n_br_valor_seguro': seguro,
            'l10n_br_valor_frete': frete,
            'l10n_br_outras_despesas': despesas,
            'l10n_br_valor_aduana': aduana
        })
        return frete, seguro, despesas, aduana

    def calc_total_amount(self):
        amount = 0
        for line in self.order_line:
            if line.product_id.l10n_br_fiscal_type == 'product':
                amount += line.l10n_br_valor_bruto
        return amount

    @api.onchange('l10n_br_total_despesas', 'l10n_br_total_seguro',
                  'l10n_br_total_frete', 'l10n_br_total_despesas_aduana')
    def _onchange_despesas_frete_seguro(self):
        amount = self.calc_total_amount()
        sub_frete = self.l10n_br_total_frete
        sub_seguro = self.l10n_br_total_seguro
        sub_aduana = self.l10n_br_total_despesas_aduana
        sub_desp = self.l10n_br_total_despesas
        for l in self.order_line:
            if l.product_id.l10n_br_fiscal_type == 'service':
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
                'l10n_br_valor_seguro':
                    self.order_line[0].l10n_br_valor_seguro + sub_seguro,
                'l10n_br_valor_frete':
                    self.order_line[0].l10n_br_valor_frete + sub_frete,
                'l10n_br_outras_despesas':
                    self.order_line[0].l10n_br_outras_despesas + sub_desp,
                'l10n_br_valor_aduana':
                    self.order_line[0].l10n_br_valor_aduana + sub_aduana
                })

    l10n_br_total_despesas = fields.Float(
        string='Despesas ( + )', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]},
        oldname='total_despesas')
    l10n_br_total_despesas_aduana = fields.Float(
        string='Despesas Aduaneiras', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]},
        oldaname='total_despesas_aduana')
    l10n_br_total_seguro = fields.Float(
        string='Seguro ( + )', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]},
        oldname='total_seguro')
    l10n_br_total_frete = fields.Float(
        string='Frete ( + )', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]},
        oldname='total_frete')


class PuchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'br.localization.filtering']

    l10n_br_valor_seguro = fields.Float(
        'Seguro', default=0.0, digits=dp.get_precision('Account'),
        oldname='valor_seguro')
    l10n_br_outras_despesas = fields.Float(
        'Despesas', default=0.0, digits=dp.get_precision('Account'),
        oldanme='outras_despesas')
    l10n_br_valor_frete = fields.Float(
        'Frete', default=0.0, digits=dp.get_precision('Account'),
        oldname='valor_frete')
    l10n_br_valor_aduana = fields.Float(
        default=0.0, digits=dp.get_precision('Account'),
        oldname='valor_aduana')

    def _prepare_tax_context(self):
        res = super(PuchaseOrderLine, self)._prepare_tax_context()
        res.update({
            'valor_frete': self.l10n_br_valor_frete,
            'valor_seguro': self.l10n_br_valor_seguro,
            'outras_despesas': self.l10n_br_outras_despesas,
            'ii_despesas': self.l10n_br_valor_aduana,
            'fiscal_type': self.l10n_br_fiscal_position_type,
        })
        return res

    @api.multi
    def _get_stock_move_price_unit(self):
        price = super(PuchaseOrderLine, self)._get_stock_move_price_unit()
        price = price + \
            (self.l10n_br_valor_frete/self.product_qty) + \
            (self.l10n_br_valor_seguro/self.product_qty) + \
            (self.l10n_br_outras_despesas/self.product_qty)
        return price
