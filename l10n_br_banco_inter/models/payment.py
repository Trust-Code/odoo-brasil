import requests
import base64
from datetime import datetime
from odoo import fields, models
from odoo.exceptions import UserError


class BoletoSicoob(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("boleto-inter", "Boleto Banco Inter")])


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    boleto_pdf = fields.Binary(string="Boleto PDF")

    def cron_check_boletos_inter(self):
        pass