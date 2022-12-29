from odoo import models, fields


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    acc_number_dig = fields.Char(string="Dígito da Conta")
    bra_number = fields.Char(string="Agência")
    bra_number_dig = fields.Char(string="Dígito da Agência")
