import base64
import json
import tempfile
from datetime import datetime, timedelta

from odoo import models
from odoo.exceptions import UserError
from requests import Session

BASE_URL = "https://cdpj.partners.bancointer.com.br/"
SCOPE = {
    "cobranca_add": "boleto-cobranca.write",
    "cobranca_cancel": "boleto-cobranca.write",
    "cobranca_get": "boleto-cobranca.read",
    "extrato.read": "extrato.read",
    "extrato-read": "extrato-read",
}


class BancoInter(models.AbstractModel):
    _name = "banco.inter.mixin"
    _description = "Banco Inter Operations"

    def _generate_cert_files(self, journal_id):
        """ Generate the temp files for cert and key.

        :param  journal_id (obj): Banco Inter Journal

        :return (str, str): (certificate_path, key_path)
        """
        cert = base64.b64decode(journal_id.l10n_br_inter_cert)
        key = base64.b64decode(journal_id.l10n_br_inter_key)

        cert_path = tempfile.mkstemp()[1]
        key_path = tempfile.mkstemp()[1]

        arq_temp = open(cert_path, "w")
        arq_temp.write(cert.decode())
        arq_temp.close()

        arq_temp = open(key_path, "w")
        arq_temp.write(key.decode())
        arq_temp.close()

        return (cert_path, key_path)

    def _generate_header(self, token):
        """_generate_header.

        :param token (str): Banco Inter access token

        :return (dict): header for request
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {token}".format(token=token),
        }

    def _prepare_session_request(self, journal_id):
        """_prepare_session_request.

        :param  journal_id (obj): Banco Inter Journal

        :return Session (obj): Return a prepared session for request
        """
        session = Session()
        session.verify = False
        session.cert = self._generate_cert_files(journal_id)
        return session

    def _check_existing_token(self):
        IrParamSudo = self.env['ir.config_parameter'].sudo()
        expiration = IrParamSudo.get_param('bancointer.token.expiration')
        if not expiration:
            return False
        expiration = datetime.fromisoformat(expiration)
        if expiration < datetime.now():
            return False
        token = IrParamSudo.get_param('bancointer.token')
        return token

    def _save_token(self, token):
        IrParamSudo = self.env['ir.config_parameter'].sudo()
        IrParamSudo.set_param('bancointer.token', token)
        expiration = datetime.now() + timedelta(hours=1)
        IrParamSudo.set_param('bancointer.token.expiration', expiration.isoformat())

    def _get_token(self, journal_id, scope):
        """ Get the Banco Inter access token

        :param journal_id (obj): Banco Inter Journal
        :param scope (str): Token Scope [cobranca_add, cobranca_cancel, cobranca_get]

        :return (str): access_token
        """
        token = self._check_existing_token()
        if token:
            return token

        url = BASE_URL + 'oauth/v2/token'
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        client_id = journal_id.l10n_br_inter_client_id
        client_secret = journal_id.l10n_br_inter_client_secret

        body = (
            "client_id={client_id}&" +
            "client_secret={client_secret}&" +
            "scope={scope}&" +
            "grant_type=client_credentials").format(
            client_id=client_id, client_secret=client_secret, scope=SCOPE[scope])

        session = self._prepare_session_request(journal_id)
        response = session.post(url, headers=headers, data=body)
        response.raise_for_status()
        token = response.json().get("access_token")
        self._save_token(token)
        return token

    def add_boleto_inter(self, journal_id, vals):
        """Add new bank slip to Banco Inter

        :param  journal_id (obj): Banco Inter Journal
        :param vals (dict): Values to create the bank slip

        :return nosso_numero (str): Bank slip ID in Banco Inter
        """
        token = self._get_token(journal_id, "cobranca_add")
        url = BASE_URL + "cobranca/v2/boletos"

        headers = self._generate_header(token)
        session = self._prepare_session_request(journal_id)

        response = session.post(url, headers=headers, data=json.dumps(vals))

        if response.status_code == 200:
            return response.json().get("nossoNumero")
        elif response.status_code == 401:
            raise UserError(
                "Erro de autorização ao consultar a API do Banco Inter")
        else:
            raise UserError(
                'Houve um erro com a API do Banco Inter:\n%s' % response.text)

    def cancel_boleto_inter(self, journal_id, acquirer_reference):
        """ Cancel bank slip in Banco Inter

        :param  journal_id (obj): Banco Inter Journal
        :param acquirer_reference (str): Bank slip ID in Banco Inter

        :return: True
        """
        url = BASE_URL + \
            "cobranca/v2/boletos/{nosso_numero}/cancelar".format(
                nosso_numero=acquirer_reference)

        token = self._get_token(journal_id, "cobranca_cancel")
        headers = self._generate_header(token)
        vals = {
            "motivoCancelamento": "SUBSTITUICAO"
        }
        session = self._prepare_session_request(journal_id)

        response = session.post(url, headers=headers, data=json.dumps(vals))

        if response.status_code != 204:
            raise UserError(
                'Houve um erro com a API do Banco Inter:\n%s' % response.text)

        return True

    def get_boleto_inter_status(self, journal_id, acquirer_reference):
        """ Get the bank slip status in Banco Inter

        :param  journal_id (obj): Banco Inter Journal
        :param acquirer_reference (str): Bank slip ID in Banco Inter

        :return (str): Bank slip status
        """
        url = BASE_URL + \
            "cobranca/v2/boletos/{nosso_numero}".format(
                nosso_numero=acquirer_reference)

        token = self._get_token(journal_id, "cobranca_get")
        headers = self._generate_header(token)
        session = self._prepare_session_request(journal_id)

        response = session.get(url, headers=headers)

        if response.status_code != 200:
            return ""

        return response.json().get("situacao")

    def get_boleto_inter_pdf(self, journal_id, acquirer_reference):
        """ Get the bank slip PDF in Banco Inter

        :param  journal_id (obj): Banco Inter Journal
        :param acquirer_reference (str): Bank slip ID in Banco Inter

        :return (str): Bank slip PDF
        """
        url = BASE_URL + \
            "cobranca/v2/boletos/{nosso_numero}/pdf".format(
                nosso_numero=acquirer_reference)

        # Get the token
        token = self._get_token(journal_id, "cobranca_get")
        headers = self._generate_header(token)
        session = self._prepare_session_request(journal_id)

        response = session.get(url, headers=headers)

        if response.status_code != 200:
            return ""

        return response.json().get("pdf")

    def get_bank_statement_inter(self, journal_id, start_date, end_date):
        """ Get the bank statement for Banco Inter

        :param  journal_id (obj): Banco Inter Journal
        :param start_date (str): Start date
        :param end_date (str): End date

        :return (list): transaction list
        """
        url = BASE_URL + "banking/v2/extrato"

        # Get the token
        token = self._get_token(journal_id, "extrato.read")
        headers = self._generate_header(token)
        session = self._prepare_session_request(journal_id)

        # Get the transaction list
        params = {"dataInicio": start_date.strftime("%Y-%m-%d"), "dataFim": end_date.strftime("%Y-%m-%d")}
        response = session.get(url, headers=headers, params=params)
        response.raise_for_status()
        transactions = response.json()["transacoes"]

        url = BASE_URL + "banking/v2/saldo"

        # Get the end balance of the day before
        start = start_date - timedelta(days=1)

        params = {"dataSaldo": start.strftime("%Y-%m-%d")}
        response = session.get(url, headers=headers, params=params)
        response.raise_for_status()
        start_balance = response.json()["disponivel"]

        params = {"dataSaldo": end_date.strftime("%Y-%m-%d")}
        response = session.get(url, headers=headers, params=params)
        response.raise_for_status()
        end_balance = response.json()["disponivel"]

        return {"start_balance": start_balance, "end_balance": end_balance, "transactions": transactions}
