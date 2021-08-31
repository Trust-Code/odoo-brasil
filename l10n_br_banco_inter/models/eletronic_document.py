import re
import base64
import requests
import tempfile
import base64
from odoo import models

class EletronicDocument(models.Model):
    _inherit = 'eletronic.document'

    def _find_attachment_ids_email(self):
        atts = super(EletronicDocument, self)._find_attachment_ids_email()
        for transaction in self.move_id.transaction_ids.filtered(lambda x: x.state in ("draft", "pending")):
            if transaction.acquirer_id.provider != 'boleto-inter':
                continue
            url = "https://apis.bancointer.com.br/openbanking/v1/certificado/boletos/%s/pdf" % transaction.acquirer_reference
            response = self.execute_request_inter(url, transaction.acquirer_id)
            if response.status_code != 200:  # Vamos ignorar
                continue
            filename = "%s - Boleto - %s.%s" % (self.numero, self.partner_id.name_get()[0][1], "pdf")
            boleto_id = self.env['ir.attachment'].create(dict(
                name=filename,
                datas=response.text,
                mimetype='application/pdf',
                res_model='account.move',
                res_id=self.move_id.id,
            ))
            atts.append(boleto_id.id)

        return atts

    def execute_request_inter(self, url, acquirer):
        headers = {
            "x-inter-conta-corrente": re.sub("[^0-9]", "", acquirer.journal_id.bank_account_id.acc_number)
        }
        cert = base64.b64decode(acquirer.journal_id.l10n_br_inter_cert)
        key = base64.b64decode(acquirer.journal_id.l10n_br_inter_key)

        cert_path = tempfile.mkstemp()[1]
        key_path = tempfile.mkstemp()[1]

        arq_temp = open(cert_path, "w")
        arq_temp.write(cert.decode())
        arq_temp.close()

        arq_temp = open(key_path, "w")
        arq_temp.write(key.decode())
        arq_temp.close()
        return requests.get(url, headers=headers, cert=(cert_path, key_path))

