# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountPaymentConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    module_payment_cielo = fields.Boolean(
        string='Manage Payments Using Cielo',
        help='-It installs the module payment_cielo.')
