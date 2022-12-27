import uuid
import base64
import requests

from datetime import datetime, timedelta

from odoo import fields, models
from odoo.exceptions import UserError

URL = "https://api.itau.com.br/cash_management/v2/"
URL_SANDBOX = (
    "https://devportal.itau.com.br/sandboxapi/cash_management_ext_v2/v2"
)


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(
        selection_add=[("boleto-itau", "Boleto Banco Itau")],
        ondelete={"boleto-itau": "set default"},
    )


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    boleto_pdf = fields.Binary(string="Boleto PDF")
    l10n_br_itau_flow = fields.Char(
        string="Itau Flow ID", default=lambda self: str(uuid.uuid4())
    )
    l10n_br_itau_barcode = fields.Char(string="Código de Barras Boleto")
    l10n_br_itau_digitavel = fields.Char(string="Linha Digitável Boleto")
    l10n_br_itau_nosso_numero = fields.Char(string="Nosso Número Itaú")

    def execute_request_itau(self, method, endpoint, data={}):
        access_token = self.get_itau_access_token()
        headers = {
            "x-itau-apikey": access_token,
            "x-itau-correlationID": str(uuid.uuid4()),
            "x-itau-flowID": self.l10n_br_itau_flow,
        }
        if self.acquirer_id.state != "enabled":
            headers.pop("x-itau-apikey")
            headers["x-sandbox-token"] = access_token
        url = (
            URL if self.acquirer_id.state == "enabled" else URL_SANDBOX
        ) + endpoint
        response = requests.request(method, url, json=data, headers=headers)
        if response.status_code == 401:
            raise UserError(
                "Erro de autorização ao consultar a API do Banco Itaú"
            )
        if response.status_code not in (200, 204):
            raise UserError(
                "Houve um erro com a API do Banco Itaú:\n%s" % response.text
            )
        return response.json()

    def action_verify_transaction(self):
        if self.acquirer_id.provider != "boleto-itau":
            return super(PaymentTransaction, self).action_verify_transaction()
        if not self.acquirer_reference:
            raise UserError(
                "Esta transação não foi enviada a nenhum gateway de pagamento"
            )

        journal = (
            self.acquirer_id.journal_id or self.invoice_ids.payment_journal_id
        )

        url = "https://secure.api.cloud.itau.com.br/boletoscash/v2/boletos?id_beneficiario={}&codigo_carteira={}&nosso_numero={}".format(
            journal.bank_account_id.acc_number,
            journal.l10n_br_itau_carteira,
            self.l10n_br_itau_nosso_numero,
        )
        access_token = self.get_itau_access_token()
        headers = {
            "x-itau-apikey": access_token,
            "x-itau-correlationID": str(uuid.uuid4()),
            "x-itau-flowID": self.l10n_br_itau_flow,
        }
        response = requests.request("GET", url, headers=headers)
        response_json = response.json()

        dados_boleto = response_json.get("dado_boleto", {}).get(
            "dados_individuais_boleto", []
        )

        if dados_boleto.get("situacao_geral_boleto") == "Pago":
            self._set_transaction_done()
            self._post_process_after_done()
        elif dados_boleto.get("situacao") == "Baixado":
            self._set_transaction_cancel()

    def action_cancel_transaction(self):
        if self.acquirer_id.provider != "boleto-itau":
            return super(PaymentTransaction, self).action_cancel_transaction()

        self._set_transaction_cancel()
        endpoint = "boletos/{}/baixa".format(self.acquirer_reference)
        self.execute_request_itau("PATCH", endpoint)

    def get_itau_access_token(self):
        journal = (
            self.acquirer_id.journal_id or self.invoice_ids.payment_journal_id
        )
        if (
            not journal.l10n_br_itau_token_expiry
            or journal.l10n_br_itau_token_expiry < datetime.now()
        ):
            url = "https://devportal.itau.com.br/api/jwt"
            res = requests.request(
                "POST",
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "client_id": journal.l10n_br_itau_client_id,
                    "client_secret": journal.l10n_br_itau_client_secret,
                },
            )
            if res.ok:
                journal.write(
                    {
                        "l10n_br_itau_access_token": res.json().get(
                            "access_token"
                        ),
                        "l10n_br_itau_token_expiry": datetime.now()
                        + timedelta(
                            seconds=res.json().get("expires_in") - 60
                        ),
                    }
                )
            else:
                raise UserError(res.text)
        return journal.l10n_br_itau_access_token

    def action_get_pdf_inter(self):
        attachment_ids = []
        for transaction in self:
            if transaction.acquirer_id.provider != "boleto-itau":
                continue
            report = self.env.ref(
                "l10n_br_banco_itau.action_report_boleto_itau"
            )
            template, _ = report._render_qweb_pdf(transaction.ids)

            filename = "%s - Boleto - %s.%s" % (
                transaction.partner_id.name_get()[0][1],
                transaction.reference,
                "pdf",
            )

            boleto_id = self.env["ir.attachment"].create(
                dict(
                    name=filename,
                    datas=base64.b64encode(template),
                    mimetype="application/pdf",
                    res_model="account.move",
                    res_id=transaction.invoice_ids
                    and transaction.invoice_ids[0].id
                    or False,
                )
            )
            attachment_ids.append(boleto_id.id)
        return attachment_ids
