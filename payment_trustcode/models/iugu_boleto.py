import re
import logging
import datetime

from odoo import api, fields, models
from odoo.http import request
from odoo.exceptions import UserError
from werkzeug import urls

_logger = logging.getLogger(__name__)
odoo_request = request

try:
    import iugu
except ImportError:
    _logger.exception("Não é possível importar iugu")


class IuguBoleto(models.Model):
    _inherit = "payment.acquirer"

    def _default_return_url(self):
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        return "%s%s" % (base_url, "/payment/process")

    provider = fields.Selection(selection_add=[("iugu", "Iugu")], ondelete = { 'iugu' : 'set default' })
    iugu_api_key = fields.Char("Iugu Api Token")
    return_url = fields.Char(
        string="Url de Retorno", default=_default_return_url, size=300
    )

    def iugu_form_generate_values(self, values):
        """ Função para gerar HTML POST do Iugu """
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )
        # ngrok_url = 'http://b2a48696.ngrok.io'

        partner_id = values.get('billing_partner')

        items = [{
            "description": 'Fatura Ref: %s' % values.get('reference'),
            "quantity": 1,
            "price_cents":  int(values.get('amount') * 100),
        }]

        today = datetime.date.today()

        invoice_data = {
            "email": partner_id.email,
            "due_date": today.strftime("%d/%m/%Y"),
            "return_url": urls.url_join(base_url, "/payment/process"),
            "notification_url": urls.url_join(  # ngrok_url
                base_url, "/iugu/notificacao/"
            ),
            "items": items,
            "payer": {
                "name": partner_id.name,
                "cpf_cnpj": partner_id.l10n_br_cnpj_cpf,
                "address": {
                    "street": partner_id.street,
                    "city": partner_id.city_id.name,
                    "number": partner_id.l10n_br_number,
                    "zip_code": re.sub('[^0-9]', '', partner_id.zip or ''),
                },
            },
        }

        iugu.config(token=self.iugu_api_key)
        invoice = iugu.Invoice()
        result = invoice.create(invoice_data)
        if "errors" in result:
            if isinstance(result["errors"], str):
                msg = result['errors']
            else:
                msg = "\n".join(
                    ["A integração com IUGU retornou os seguintes erros"] +
                    ["Field: %s %s" % (x[0], x[1][0])
                     for x in result['errors'].items()])
            raise UserError(msg)

        acquirer_reference = result.get("id")
        payment_transaction_id = self.env['payment.transaction'].search(
            [("reference", "=", values['reference'])])

        payment_transaction_id.write({
            "acquirer_reference": acquirer_reference,
            "invoice_url": result['secure_url'],
        })

        url = result.get("secure_url")
        return {
            "checkout_url": urls.url_join(
                base_url, "/iugu/checkout/redirect"),
            "secure_url": url
        }


class TransactionIugu(models.Model):
    _inherit = "payment.transaction"

    invoice_url = fields.Char(string="Fatura IUGU", size=300)

    @api.model
    def _iugu_form_get_tx_from_data(self, data):
        acquirer_reference = data.get("data[id]")
        tx = self.search([("acquirer_reference", "=", acquirer_reference)])
        return tx[0]

    def _iugu_form_validate(self, data):
        status = data.get("data[status]")

        if status in ('paid', 'partially_paid', 'authorized'):
            self._set_transaction_done()
            return True
        elif status == 'pending':
            self._set_transaction_pending()
            return True
        else:
            self._set_transaction_cancel()
            return False
