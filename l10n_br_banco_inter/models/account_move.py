import re
import base64
import requests
import tempfile
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
    

class AccountMove(models.Model):
    _inherit = 'account.move'

    def validate_data_boleto(self):
        errors = []
        for invoice in self:
            if not invoice.payment_journal_id or not self.payment_journal_id.l10n_br_use_boleto_inter:
                continue

            partner = invoice.partner_id.commercial_partner_id
            if partner.is_company and not partner.l10n_br_legal_name:
                errors.append('Destinatário - Razão Social')
            if not partner.street:
                errors.append('Destinatário / Endereço - Rua')
            if not partner.l10n_br_number:
                errors.append('Destinatário / Endereço - Número')
            if not partner.zip or len(re.sub(r"\D", "", partner.zip)) != 8:
                errors.append('Destinatário / Endereço - CEP')
            if not partner.state_id:
                errors.append(u'Destinatário / Endereço - Estado')
            if not partner.city_id:
                errors.append(u'Destinatário / Endereço - Município')
            if not partner.country_id:
                errors.append(u'Destinatário / Endereço - País')
        if len(errors) > 0:
            msg = "\n".join(
                ["Por favor corrija os erros antes de prosseguir"] + errors)
            raise ValidationError(msg)

    def send_information_to_banco_inter(self):
        if not self.payment_journal_id or not self.payment_journal_id.l10n_br_use_boleto_inter:
            return

        for moveline in self.receivable_move_line_ids:
            acquirer = self.env['payment.acquirer'].search([('provider', '=', 'boleto-inter')])
            if not acquirer:
                raise UserError('Configure o modo de pagamento do Boleto Banco Inter')
            transaction = self.env['payment.transaction'].create({
                'acquirer_id': acquirer.id,
                'amount': moveline.amount_residual,
                'currency_id': moveline.move_id.currency_id.id,
                'partner_id': moveline.partner_id.id,
                'type': 'server2server',
                'date_maturity': moveline.date_maturity,
                'invoice_ids': [(6, 0, self.ids)],
            })

            url = "https://apis.bancointer.com.br/openbanking/v1/certificado/boletos"

            instrucao = self.payment_journal_id.l10n_br_boleto_instrucoes or ''

            tipo_mora = "ISENTO"
            if self.payment_journal_id.l10n_br_valor_juros_mora:
                tipo_mora = "TAXAMENSAL"
            tipo_multa = "NAOTEMMULTA"
            if self.payment_journal_id.l10n_br_valor_multa:
                tipo_multa = "PERCENTUAL"  # Percentual

            partner_id = self.partner_id.commercial_partner_id
            vals = {
                "pagador":{
                    "cnpjCpf": re.sub("[^0-9]", "",partner_id.l10n_br_cnpj_cpf),
                    "nome": partner_id.l10n_br_legal_name or partner_id.name,
                    "email": self.partner_id.email or "",
                    "telefone":"",
                    "ddd":"",
                    "cep": re.sub("[^0-9]", "", partner_id.zip),
                    "numero": partner_id.l10n_br_number,
                    "complemento": partner_id.street2 or "",
                    "bairro": partner_id.l10n_br_district,
                    "cidade": partner_id.city_id.name,
                    "uf": partner_id.state_id.code,
                    "endereco": partner_id.street,
                    "tipoPessoa": "FISICA" if partner_id.company_type == "person" else "JURIDICA"
                },
                "dataEmissao": transaction.create_date.date().isoformat(),
                "seuNumero": transaction.reference,
                "dataVencimento": moveline.date_maturity.isoformat(),
                "mensagem": {
                    "linha1": "",
                },
                "desconto1":{
                    "codigoDesconto": "NAOTEMDESCONTO",
                    "taxa": 0,
                    "valor": 0,
                    "data": ""
                },
                "desconto2": {
                    "codigoDesconto": "NAOTEMDESCONTO",
                    "taxa": 0,
                    "valor": 0,
                    "data": ""
                },
                "desconto3":{
                    "codigoDesconto": "NAOTEMDESCONTO",
                    "taxa": 0,
                    "valor": 0,
                    "data": ""
                },
                "valorNominal": moveline.amount_residual,
                "valorAbatimento": 0,
                "multa": {
                    "codigoMulta": tipo_multa,
                    "data": (moveline.date_maturity + timedelta(days=1)).isoformat(),
                    "taxa": self.payment_journal_id.l10n_br_valor_multa,
                    "valor": 0,
                },
                "mora": {
                    "codigoMora": tipo_mora,
                    "data": (moveline.date_maturity + timedelta(days=1)).isoformat(),
                    "taxa": self.payment_journal_id.l10n_br_valor_juros_mora,
                    "valor": 0,
                },
                "cnpjCPFBeneficiario": re.sub("[^0-9]", "", self.company_id.l10n_br_cnpj_cpf),
                "numDiasAgenda": "SESSENTA",
                "dataLimite": "SESSENTA",
            }
            headers = {
                "x-inter-conta-corrente": re.sub("[^0-9]", "", self.payment_journal_id.bank_account_id.acc_number)
            }
            cert = base64.b64decode(self.payment_journal_id.l10n_br_inter_cert)
            key = base64.b64decode(self.payment_journal_id.l10n_br_inter_key)

            cert_path = tempfile.mkstemp()[1]
            key_path = tempfile.mkstemp()[1]

            arq_temp = open(cert_path, "w")
            arq_temp.write(cert.decode())
            arq_temp.close()

            arq_temp = open(key_path, "w")
            arq_temp.write(key.decode())
            arq_temp.close()

            response = requests.post(url, json=vals, headers=headers, cert=(cert_path, key_path))
            if response.status_code == 200:
                json_p = response.json()
                nosso_numero = json_p["nossoNumero"]
                linha_digitavel = json_p["linhaDigitavel"]
                codigo_barras = json_p["codigoBarras"]
            elif response.status_code == 401:
                raise UserError("Erro de autorização ao consultar a API do Banco Inter")
            else:
                raise UserError('Houve um erro com a API do Banco Inter:\n%s' % response.text)

            transaction.write({
                'acquirer_reference': nosso_numero,
            })

    def generate_boleto_banco_inter_transactions(self):
        for item in self:
            item.send_information_to_banco_inter()

    def action_post(self):
        self.validate_data_boleto()
        result = super(AccountMove, self).action_post()
        self.generate_boleto_banco_inter_transactions()
        return result
