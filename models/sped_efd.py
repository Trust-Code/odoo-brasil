# -*- coding: utf-8 -*-


from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'
    
    
    natureza_operacao = fields.Char('Natureza Operação')
