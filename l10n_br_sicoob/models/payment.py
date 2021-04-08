import requests
import base64
from datetime import datetime
from odoo import fields, models
from odoo.exceptions import UserError


class BoletoSicoob(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("sicoob-boleto", "Boleto Sicoob")])


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    boleto_pdf = fields.Binary(string="Boleto PDF")