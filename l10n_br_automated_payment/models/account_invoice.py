# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import re
import iugu
from odoo import api, models
from odoo.exceptions import ValidationError, UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def validate_data_iugu(self):
        errors = []
        for invoice in self:
            partner = invoice.partner_id.commercial_partner_id
            if not self.env.user.company_id.iugu_api_token:
                errors.append('Configure o token de API do Iugu')
            if partner.is_company and not partner.legal_name:
                errors.append('Destinatário - Razão Social')
            if not partner.street:
                errors.append('Destinatário / Endereço - Rua')
            if not partner.number:
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

    def send_information_to_iugu(self):
        for invoice in self:

            token = self.env.user.company_id.iugu_api_token
            url_base = self.env.user.company_id.iugu_url_base
            iugu.config(token=token)
            iugu_invoice_api = iugu.Invoice()

            for moveline in invoice.receivable_move_line_ids:
                if not moveline.payment_mode_id.receive_by_iugu:
                    continue

                invoice.partner_id.action_synchronize_iugu()
                vals = {
                    'email': invoice.partner_id.email,
                    'due_date': moveline.date_maturity.strftime('%Y-%m-%d'),
                    'ensure_workday_due_date': True,
                    'items': [{
                        'description': 'Fatura Ref: %s - %s' % (
                            moveline.move_id.name, moveline.name),
                        'quantity': 1,
                        'price_cents': int(moveline.amount_residual * 100),
                    }],
                    'return_url': '%s/my/invoices/%s' % (url_base, invoice.id),
                    'notification_url': '%s/iugu/webhook?id=%s' % (
                        url_base, invoice.id),
                    'fines': True,
                    'late_payment_fine': 2,
                    'per_day_interest': True,
                    'customer_id': invoice.partner_id.iugu_id,
                    'early_payment_discount': False,
                    'order_id': invoice.name,
                }
                data = iugu_invoice_api.create(vals)
                if "errors" in data:
                    msg = "\n".join(
                        ["A integração com IUGU retornou os seguintes erros"] +
                        ["Field: %s %s" % (x[0], x[1][0])
                         for x in data['errors'].items()])
                    raise UserError(msg)
                moveline.write({
                    'iugu_id': data['id'],
                    'iugu_secure_payment_url': data['secure_url'],
                    'iugu_digitable_line': data['bank_slip']['digitable_line'],
                    'iugu_barcode_url': data['bank_slip']['barcode'],
                })

    @api.multi
    def action_invoice_open(self):
        self.validate_data_iugu()
        result = super(AccountInvoice, self).action_invoice_open()
        self.send_information_to_iugu()
        return result
