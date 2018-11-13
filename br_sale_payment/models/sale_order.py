# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'br.localization.filtering']

    l10n_br_payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string=u"Modo de pagamento")

    @api.multi
    def _prepare_invoice(self):
        vals = super(SaleOrder, self)._prepare_invoice()
        vals['l10n_br_payment_mode_id'] = self.l10n_br_payment_mode_id.id
        return vals
