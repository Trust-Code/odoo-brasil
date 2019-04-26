# © 2019 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_payment_mode_id = fields.Many2one(
        string="Modo de pagamento",
        company_dependent=True,
        domain=[('type', '=', 'receivable')],
        comodel_name='l10n_br.payment.mode')

    @api.model
    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + \
            ['property_payment_mode_id']
