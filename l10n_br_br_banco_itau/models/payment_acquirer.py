
from odoo import fields, models


class PaymentAcquire(models.Model):
    _inherit = 'payment.acquirer'
    
    provider = fields.Selection(selection_add=[("boleto-itau", "Boleto Banco Itau")], ondelete = { 'boleto-itau' : 'set default' })
