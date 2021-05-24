import re
import base64
import requests
import tempfile
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

    def execute_request_inter(self, method, url, vals):
        headers = {
            "x-inter-conta-corrente": re.sub("[^0-9]", "", self.acquirer_id.journal_id.bank_account_id.acc_number)
        }
        cert = base64.b64decode(self.acquirer_id.journal_id.l10n_br_inter_cert)
        key = base64.b64decode(self.acquirer_id.journal_id.l10n_br_inter_key)

        cert_path = tempfile.mkstemp()[1]
        key_path = tempfile.mkstemp()[1]

        arq_temp = open(cert_path, "w")
        arq_temp.write(cert.decode())
        arq_temp.close()

        arq_temp = open(key_path, "w")
        arq_temp.write(key.decode())
        arq_temp.close()
        response = requests.request(method, url, json=vals, headers=headers, cert=(cert_path, key_path))
        if response.status_code == 401:
            raise UserError("Erro de autorização ao consultar a API do Banco Inter")
        if response.status_code not in (200, 204):
            raise UserError('Houve um erro com a API do Banco Inter:\n%s' % response.text)
        return response

    def action_verify_transaction(self):
        if self.acquirer_id.provider != 'boleto-inter':
            return super(PaymentTransaction, self).action_verify_transaction()
        if not self.acquirer_reference:
            raise UserError('Esta transação não foi enviada a nenhum gateway de pagamento')

        url = "https://apis.bancointer.com.br/openbanking/v1/certificado/boletos/%s" % self.acquirer_reference
        response = self.execute_request_inter("GET", url, None)
        json_p = response.json()

        if json_p.get("situacao") == "PAGO":
            self._set_transaction_done()
            self._post_process_after_done()
        elif json_p.get("situacao") == "BAIXADO":
            self._set_transaction_cancel()

    def action_cancel_transaction(self):
        if self.acquirer_id.provider != 'boleto-inter':
            return super(PaymentTransaction, self).action_cancel_transaction()

        self._set_transaction_cancel()
        url = "https://apis.bancointer.com.br/openbanking/v1/certificado/boletos/%s/baixas" % self.acquirer_reference
        vals = {
            "codigoBaixa": "SUBISTITUICAO"
        }
        self.execute_request_inter("POST", url, vals)
