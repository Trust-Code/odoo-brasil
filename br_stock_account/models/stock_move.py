import math
from odoo import fields, models, api, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    def should_round_down(self, val):
        if val < 0:
            return ((val * -1) % 1) < 0.5
        return (val % 1) < 0.5

    def round_value(self, val, ndigits=0):
        if ndigits > 0:
            val *= 10 ** (ndigits - 1)

        is_positive = val > 0
        tmp_val = val
        if not is_positive:
            tmp_val *= -1

        rounded_value = math.floor(tmp_val) if self.should_round_down(val) else math.ceil(tmp_val)
        if not is_positive:
            rounded_value *= -1

        if ndigits > 0:
            rounded_value /= 10 ** (ndigits - 1)

        return rounded_value

    @api.multi
    def _get_price_unit(self):
        """Retorna o preço unitário para a movimentação"""
        self.ensure_one()

        res = super(StockMove, self)._get_price_unit()

        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            line = self.purchase_line_id
            res += self.round_value(((line.valor_frete + line.outras_despesas) / line.product_qty), 5)

        return res