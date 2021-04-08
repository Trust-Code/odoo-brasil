import re
import base64
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
    

class AccountMove(models.Model):
    _inherit = 'account.move'

    def validate_data_boleto(self):
        errors = []
        for invoice in self:
            if not invoice.payment_journal_id or not self.payment_journal_id.l10n_br_emitir_boleto:
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

    def send_information_to_sicoob(self):
        if not self.payment_journal_id or not self.payment_journal_id.l10n_br_emitir_boleto:
            return

        for moveline in self.receivable_move_line_ids:
            acquirer = self.env['payment.acquirer'].search([('provider', '=', 'sicoob-boleto')])
            if not acquirer:
                raise UserError('Configure o modo de pagamento do Sicoob')
            transaction = self.env['payment.transaction'].create({
                'acquirer_id': acquirer.id,
                'amount': moveline.amount_residual,
                'currency_id': moveline.move_id.currency_id.id,
                'partner_id': moveline.partner_id.id,
                'type': 'server2server',
                'date_maturity': moveline.date_maturity,
                'invoice_ids': [(6, 0, self.ids)],
            })

            if acquirer.state == 'enabled':
                url = 'https://api.sisbr.com.br/cooperado'
            else:
                url = 'https://sandbox.sicoob.com.br'

            instrucao = self.payment_journal_id.l10n_br_boleto_instrucoes or ''
            instrucoes = instrucao.split('\n')

            tipo_mora = 3 # Isento
            if self.payment_journal_id.l10n_br_valor_juros_mora:
                tipo_mora = 2  # Taxa Mensal
            tipo_multa = 0  # Isento
            if self.payment_journal_id.l10n_br_valor_multa:
                tipo_multa = 2  # Percentual

            vals = {
                "numeroContrato": self.payment_journal_id.l10n_br_sicoob_contrato,
                "modalidade": 1,
                "numeroContaCorrente": self.payment_journal_id.bank_account_id.acc_number,
                "especieDocumento": "DM",
                "seuNumero": transaction.reference,
                "identificacaoBoletoEmpresa": transaction.reference,
                "identificacaoEmissaoBoleto": 2,
                "identificacaoDistribuicaoBoleto": 2,
                "valor": "%.2f" % moveline.amount_residual,
                "dataVencimento": moveline.date_maturity.isoformat(),
                "tipoMulta": tipo_multa,
                "valorMulta": self.payment_journal_id.l10n_br_valor_multa,
                "tipoJurosMora": tipo_mora,
                "valorJurosMora": self.payment_journal_id.l10n_br_valor_juros_mora,
                "numeroParcela": 1,
                "aceite": True,
                "pagador": {
                    "numeroCpfCnpj": self.partner_id.l10n_br_cnpj_cpf,
                    "nome": self.partner_id.name,
                    "endereco": self.partner_id.street,
                    "bairro": self.partner_id.l10n_br_district,
                    "cidade": self.partner_id.city_id.name,
                    "cep": self.partner_id.zip,
                    "uf": self.partner_id.state_id.code,
                    "email": self.partner_id.email
                },
                "beneficiarioFinal": {
                    "numeroCpfCnpj": self.company_id.l10n_br_cnpj_cpf,
                    "nome": self.company_id.l10n_br_legal_name,
                },
                "mensagensInstrucao": {
                    "tipoInstrucao": 1,
                    "mensagens": instrucoes,
                },
                "gerarPdf": True,
            }

            headers = {
                "Authorization": "Bearer %s" % self.payment_journal_id.l10n_br_sicoob_access_token
            }

            # Essa parte aqui precisa chamar a API do sicoob e 
            # salvar o retorno no objeto transaction
            response = requests.post("%s/cobranca-bancaria/v1/boletos" % url, json=[vals], headers=headers)
            if response.status_code == 207:
                json_p = response.json()["resultado"][0]
                boleto_pdf = json_p["boleto"]["pdfBoleto"]
                nosso_numero = json_p["boleto"]["nossoNumero"]

            elif response.status_code == 401:
                raise UserError('A autorização do Sicoob expirou, favor efetuar login novamente!')
            else:
                raise UserError('Houve um erro com a API do Sicoob:\n%s' % response.text)

            transaction.write({
                'acquirer_reference': nosso_numero,
                'boleto_pdf': boleto_pdf,
            })

    def generate_boleto_sicoob_transactions(self):
        for item in self:
            item.send_information_to_sicoob()

    def action_post(self):
        self.validate_data_boleto()
        result = super(AccountMove, self).action_post()
        self.generate_boleto_sicoob_transactions()
        return result
