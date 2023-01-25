import re
import base64
import requests
import tempfile
from datetime import timedelta
from odoo import models
from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'banco.inter.mixin']

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

        for moveline in self.receivable_move_line_ids.filtered(lambda x: not x.reconciled):
            acquirer = self.env['payment.acquirer'].search(
                [('provider', '=', 'boleto-inter')])
            if not acquirer:
                raise UserError(
                    'Configure o modo de pagamento do Boleto Banco Inter')
            transaction = self.env['payment.transaction'].create({
                'acquirer_id': acquirer.id,
                'amount': round(moveline.amount_residual, 2),
                'currency_id': moveline.move_id.currency_id.id,
                'partner_id': moveline.partner_id.id,
                'date_maturity': moveline.date_maturity,
                'invoice_ids': [(6, 0, self.ids)],
            })

            tipo_mora = "ISENTO"
            if self.payment_journal_id.l10n_br_valor_juros_mora:
                tipo_mora = "TAXAMENSAL"
            tipo_multa = "NAOTEMMULTA"
            if self.payment_journal_id.l10n_br_valor_multa:
                tipo_multa = "PERCENTUAL"  # Percentual

            partner_id = self.partner_id.commercial_partner_id
            vals = {
                "seuNumero": transaction.reference,
                "valorNominal": moveline.amount_residual,
                "dataVencimento": moveline.date_maturity.isoformat(),
                "numDiasAgenda": 60,
                "pagador": {
                    # Check the format for cpf
                    "cpfCnpj": re.sub("[^0-9]", "", partner_id.l10n_br_cnpj_cpf),
                    "tipoPessoa": "FISICA" if partner_id.company_type == "person" else "JURIDICA",
                    "nome": partner_id.l10n_br_legal_name or partner_id.name,
                    "endereco": partner_id.street,
                    "numero": partner_id.l10n_br_number,
                    "complemento": partner_id.street2 or "",
                    "bairro": partner_id.l10n_br_district,
                    "cidade": partner_id.city_id.name,
                    "uf": partner_id.state_id.code,
                    "cep": re.sub("[^0-9]", "", partner_id.zip),
                    "email": self.partner_id.email or "",
                    "ddd": "",
                    "telefone": "",
                },
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
            }

            nosso_numero = self.add_boleto_inter(self.payment_journal_id, vals)

            transaction.write({
                'acquirer_reference': nosso_numero,
            })

    def generate_payment_transactions(self):
        super(AccountMove, self).generate_payment_transactions()
        for item in self:
            item.send_information_to_banco_inter()
            if self.env.context.get("print_boleto_pdf"):
                item.transaction_ids.filtered(
                    lambda x: x.state in ("draft", "pending")
                ).action_get_pdf_inter()

    def action_post(self):
        self.validate_data_boleto()
        return super(AccountMove, self).action_post()
