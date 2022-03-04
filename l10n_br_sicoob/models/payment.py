from odoo import fields, models



class BoletoSicoob(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("sicoob-boleto", "Boleto Sicoob")], ondelete = { 'sicoob-boleto' : 'set default' })


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    boleto_pdf = fields.Binary(string="Boleto PDF")