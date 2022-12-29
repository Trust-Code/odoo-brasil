import re
import uuid
import requests
from datetime import datetime, timedelta

from odoo import models
from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def validate_data_boleto(self):
        errors = []
        for invoice in self:
            if (
                not invoice.payment_journal_id
                or not self.payment_journal_id.l10n_br_use_boleto_itau
            ):
                continue

            partner = invoice.partner_id.commercial_partner_id
            if partner.is_company and not partner.l10n_br_legal_name:
                errors.append("Destinatário - Razão Social")
            if not partner.street:
                errors.append("Destinatário / Endereço - Rua")
            if not partner.l10n_br_number:
                errors.append("Destinatário / Endereço - Número")
            if not partner.zip or len(re.sub(r"\D", "", partner.zip)) != 8:
                errors.append("Destinatário / Endereço - CEP")
            if not partner.state_id:
                errors.append("Destinatário / Endereço - Estado")
            if not partner.city_id:
                errors.append("Destinatário / Endereço - Município")
            if not partner.country_id:
                errors.append("Destinatário / Endereço - País")
        if len(errors) > 0:
            msg = "\n".join(
                ["Por favor corrija os erros antes de prosseguir"] + errors
            )
            raise ValidationError(msg)

    def send_information_to_banco_itau(self):
        if (
            not self.payment_journal_id
            or not self.payment_journal_id.l10n_br_use_boleto_itau
        ):
            return

        for moveline in self.receivable_move_line_ids.filtered(
            lambda x: not x.reconciled
        ):
            acquirer = self.env["payment.acquirer"].search(
                [("provider", "=", "boleto-itau")]
            )
            if not acquirer:
                raise UserError(
                    "Configure o modo de pagamento do Boleto Banco Itaú"
                )
            transaction = self.env["payment.transaction"].create(
                {
                    "acquirer_id": acquirer.id,
                    "amount": moveline.amount_residual,
                    "currency_id": moveline.move_id.currency_id.id,
                    "partner_id": moveline.partner_id.id,
                    "date_maturity": moveline.date_maturity,
                    "invoice_ids": [(6, 0, self.ids)],
                    "payment_journal_id": moveline.move_id.payment_journal_id.id,
                }
            )

            partner_id = self.partner_id.commercial_partner_id
            vals = {
                "etapa_processo_boleto": "efetivacao"
                if acquirer.state == "enabled"
                else "validacao",
                "beneficiario": {
                    "id_beneficiario": self.payment_journal_id.bank_account_id.acc_number
                },
                "dado_boleto": {
                    "descricao_instrumento_cobranca": "boleto",
                    "tipo_boleto": "a vista",
                    "codigo_carteira": self.payment_journal_id.l10n_br_boleto_carteira,
                    "valor_total_titulo": moveline.amount_residual,
                    "codigo_especie": "",
                    "valor_abatimento": 0,
                    "data_emissao": transaction.create_date.date().isoformat(),
                    "indicador_pagamento_parcial": False,
                },
                "pagador": {
                    "pessoa": {
                        "nome_pessoa": partner_id.l10n_br_legal_name
                        or partner_id.name,
                        "tipo_pessoa": {
                            "codigo_tipo_pessoa": "J"
                            if partner_id.is_company
                            else "F",
                            "numero_cadastro_pessoa_fisica": re.sub(
                                "[^0-9]", "", partner_id.l10n_br_cnpj_cpf
                            ),
                            "numero_cadastro_nacional_pessoa_juridica": re.sub(
                                "[^0-9]", "", partner_id.l10n_br_cnpj_cpf
                            ),
                        },
                    },
                },
                "sacador_avalista": {
                    "pessoa": {
                        "nome_pessoa": self.company_id.l10n_br_legal_name,
                        "tipo_pessoa": {
                            "codigo_tipo_pessoa": "J",
                            "numero_cadastro_nacional_pessoa_juridica": re.sub(
                                "[^0-9]", "", self.company_id.l10n_br_cnpj_cpf
                            ),
                        },
                    },
                },
                "endereco": {
                    "nome_logradouro": partner_id.street
                    or "" + partner_id.l10n_br_number
                    or "" + partner_id.street2
                    or "",
                    "nome_bairro": partner_id.l10n_br_district,
                    "nome_cidade": partner_id.city_id.name,
                    "sigla_UF": partner_id.state_id.code,
                    "email": self.partner_id.email or "",
                    "numero_CEP": re.sub("[^0-9]", "", partner_id.zip),
                },
                "dados_individuais_boleto": {
                    "data_vencimento": (
                        moveline.date_maturity + timedelta(days=1)
                    ).isoformat(),
                    "valor_titulo": moveline.amount_residual,
                    "data_limite_pagamento": (
                        moveline.date_maturity + timedelta(days=60)
                    ).isoformat(),
                },
                "texto_seu_numero": transaction.reference,
                "desconto_expresso": False,
                "juros": {
                    "codigo_tipo_juros": "90",
                    "percentual_juros": self.payment_journal_id.l10n_br_valor_boleto_juros_mora
                    or 0,
                },
                "multa": {
                    "codigo_tipo_multa": "02",
                    "percentual_multa": self.payment_journal_id.l10n_br_valor_boleto_multa
                    or 0,
                },
                "protesto": {"protesto": 4, "quantidade_dias_protesto": 1},
                "negativacao": {"negativacao": 5},
            }

            response_json = transaction.execute_request_itau(
                "POST", "/boletos", data=vals
            )

            dados_boleto = response_json.get("dado_boleto", {}).get(
                "dados_individuais_boleto", []
            )
            if dados_boleto:
                dados_boleto = dados_boleto[0]
                transaction.write(
                    {
                        "acquirer_reference": dados_boleto.get(
                            "id_boleto_individual"
                        ),
                        "l10n_br_itau_barcode": dados_boleto.get(
                            "codigo_barras"
                        ),
                        "l10n_br_itau_digitavel": dados_boleto.get(
                            "numero_linha_digitavel"
                        ),
                        "l10n_br_itau_nosso_numero": dados_boleto.get(
                            "numero_nosso_numero"
                        ),
                    }
                )

    def generate_payment_transactions(self):
        super(AccountMove, self).generate_payment_transactions()
        for item in self:
            item.send_information_to_banco_itau()

    def action_post(self):
        self.validate_data_boleto()
        return super(AccountMove, self).action_post()
