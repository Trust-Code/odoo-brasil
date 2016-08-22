

from odoo import api, fields, models


class AccountAccountTemplate(models.Model):
    _inherit = 'account.account.template'
    
    type = fields.Char(string="Type")
    parent_id = fields.Many2one('account.account.template', string="Parent")