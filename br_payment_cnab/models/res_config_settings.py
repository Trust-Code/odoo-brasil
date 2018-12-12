# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_br_multi_company_payment = fields.Boolean(
        string="Pay Bills in Head Office?")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        multi_company = params.get_param(
            'br_payment_cnab.l10n_br_multi_company_payment', default=0)
        res.update(
            l10n_br_multi_company_payment=(multi_company == 'True')
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'br_payment_cnab.l10n_br_multi_company_payment',
            self.l10n_br_multi_company_payment)
