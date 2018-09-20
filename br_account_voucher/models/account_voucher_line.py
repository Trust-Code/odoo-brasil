# -*- coding: utf-8 -*-
# © 2018 Johny Chen Jy <johnychenjy@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountVoucherLine(models.Model):
    _inherit = 'account.voucher.line'

    analytic_tag_ids = fields.Many2many('account.analytic.tag',
                                        string='Analytic Tags')
