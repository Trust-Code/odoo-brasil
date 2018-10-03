# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    interest_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Interests Account'
    )

    fine_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Fines Account'
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            interest_account_id=int(params.get_param(
                'br_payment_cnab.interest_account_id', default=0)),
            fine_account_id=int(params.get_param(
                'br_payment_cnab.fine_account_id', default=0))
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'br_payment_cnab.interest_account_id', self.interest_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'br_payment_cnab.fine_account_id', self.fine_account_id.id)
