# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def unlink(self):
        for item in self:
            line_ids = self.env['payment.order.line'].search(
                [('move_line_id', '=', item.id),
                 ('state', '=', 'draft')])
            line_ids.sudo().unlink()
        return super(AccountMoveLine, self).unlink()

    @api.multi
    def _update_check(self):
        for item in self:
            total = self.env['payment.order.line'].search_count(
                [('move_line_id', '=', item.id),
                 ('state', 'not in', ('draft', 'cancelled', 'rejected'))])
            if total > 0:
                raise UserError('Existe uma ordem de pagamento relacionada!\
                                Cancele o item da ordem primeiro')
        return super(AccountMoveLine, self)._update_check()
