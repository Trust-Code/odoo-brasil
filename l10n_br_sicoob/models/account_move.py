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
            if not invoice.payment_journal_id:
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
        if not self.payment_journal_id:
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
                url = 'https://sandbox.sicoob.com.br'  # TODO URL principal
            else:
                url = 'https://sandbox.sicoob.com.br'

            api_token = self.payment_journal_id.l10n_br_sicoob_access_token

            # instrucao = self.payment_journal_id.instrucoes or ''
            # instrucoes = [instrucao[y-95:y] for y in range(95, len(instrucao)+95, 95)]

            # TODO Esses valores aqui precisam ser preenchidos
            vals = {
                "numeroContrato": 25546454,
                "modalidade": 1,
                "numeroContaCorrente": 0,
                "especieDocumento": "DM",
                "dataEmissao": "2018-09-20T00:00:00-03:00",
                "nossoNumero": 2588658,
                "seuNumero": "1235512",
                "identificacaoBoletoEmpresa": "4562",
                "identificacaoEmissaoBoleto": 1,
                "identificacaoDistribuicaoBoleto": 1,
                "valor": 156.23,
                "dataVencimento": "2018-09-20T00:00:00-03:00",
                "dataLimitePagamento": "2018-09-20T00:00:00-03:00",
                "valorAbatimento": 1,
                "tipoDesconto": 1,
                "dataPrimeiroDesconto": "2018-09-20T00:00:00-03:00",
                "valorPrimeiroDesconto": 1,
                "dataSegundoDesconto": "2018-09-20T00:00:00-03:00",
                "valorSegundoDesconto": 0,
                "dataTerceiroDesconto": "2018-09-20T00:00:00-03:00",
                "valorTerceiroDesconto": 0,
                "tipoMulta": 0,
                "dataMulta": "2018-09-20T00:00:00-03:00",
                "valorMulta": 5,
                "tipoJurosMora": 2,
                "dataJurosMora": "2018-09-20T00:00:00-03:00",
                "valorJurosMora": 4,
                "numeroParcela": 1,
                "aceite": True,
                "codigoNegativacao": 2,
                "numeroDiasNegativacao": 60,
                "codigoProtesto": 1,
                "numeroDiasProtesto": 30,
                "pagador": {
                    "numeroCpfCnpj": "98765432185",
                    "nome": "Marcelo dos Santos",
                    "endereco": "Rua 87 Quadra 1 Lote 1 casa 1",
                    "bairro": "Santa Rosa",
                    "cidade": "Luziânia",
                    "cep": "72320000",
                    "uf": "DF",
                    "email": ["pagador@dominio.com.br"]
                },
                "beneficiarioFinal": {
                    "numeroCpfCnpj": "98784978699",
                    "nome": "Lucas de Lima"
                },
                "mensagensInstrucao": {
                    "tipoInstrucao": 1,
                    "mensagens": [
                        "Descrição da Instrução 1",
                        "Descrição da Instrução 2",
                        "Descrição da Instrução 3",
                        "Descrição da Instrução 4",
                        "Descrição da Instrução 5"
                    ]
                },
                "gerarPdf": True,
            }

            # Aqui é um exemplo de como buscar as informações
            # vals = {
            #     'boleto.emissao': self.invoice_date,
            #     'boleto.vencimento': self.invoice_date_due,
            #     'boleto.documento': self.name,
            #     'boleto.titulo': "DM",
            #     'boleto.valor': "%.2f" % self.amount_total,
            #     'boleto.pagador.nome': self.partner_id.name,
            #     'boleto.pagador.cprf': self.partner_id.l10n_br_cnpj_cpf,
            #     'boleto.pagador.endereco.cep': "%s-%s" % (self.partner_id.zip[:5], self.partner_id.zip[-3:]),
            #     'boleto.pagador.endereco.uf': self.partner_id.state_id.code,
            #     'boleto.pagador.endereco.localidade': self.partner_id.city_id.name,
            #     'boleto.pagador.endereco.bairro': self.partner_id.l10n_br_district,
            #     'boleto.pagador.endereco.logradouro': self.partner_id.street,
            #     'boleto.pagador.endereco.numero': self.partner_id.l10n_br_number,
            #     'boleto.pagador.endereco.complemento': "",
            # }

            headers = {
                "Authorization": "Bearer %s" % self.payment_journal_id.l10n_br_sicoob_access_token
            }

            # Essa parte aqui precisa chamar a API do sicoob e 
            # salvar o retorno no objeto transaction
            response = requests.post("%s/cobranca-bancaria/v1/boletos" % url, json=[vals], headers=headers)
            import ipdb; ipdb.set_trace()
            if response.status_code == 207:
                json_p = response.json()["resultado"][0]
                
                boleto_pdf = json_p["boleto"]["pdfBoleto"]

                seu_numero = json_p["boleto"]["seuNumero"]
                nosso_numero = json_p["boleto"]["nossoNumero"]
                linha_digitavel = json_p["boleto"]["linhaDigitavel"]

            else:
                print(response.text)
                jsonp = response.json()
                message = '\n'.join([x['mensagem'] for x in jsonp['erro']['causas']])
                raise UserError('Houve um erro com a API do Boleto Cloud:\n%s' % message)

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
