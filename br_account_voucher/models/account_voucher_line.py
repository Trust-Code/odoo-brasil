from odoo import models, fields


class AccountVoucherLine(models.Model):
    _inherit = 'account.voucher.line'

    analytic_tag_ids = fields.Many2many('account.analytic.tag',
                                        string='Etiquetas analíticas')
