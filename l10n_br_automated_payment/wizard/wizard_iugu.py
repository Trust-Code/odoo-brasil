# © 2020 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import iugu
from odoo import api, fields, models
from odoo.exceptions import UserError


class WizardChangeIuguInvoice(models.TransientModel):
    _name = 'wizard.change.iugu.invoice'
    _description = 'Modificar parcelamento boleto'

    payment_due = fields.Boolean(string="Pagamento Atrasado?")
    date_change = fields.Date(string='Alterar Vencimento')
    move_line_id = fields.Many2one('account.move.line', readonly=1)

    def action_change_invoice_iugu(self):
        if self.move_line_id.reconciled:
            raise UserError('O pagamento já está reconciliado')
        if self.date_change:

            token = self.env.company.iugu_api_token
            iugu.config(token=token)
            iugu_invoice_api = iugu.Invoice()

            data = iugu_invoice_api.duplicate(self.move_line_id.iugu_id, {
                'due_date': self.date_change.strftime('%Y-%m-%d'),
                'email': self.move_line_id.invoice_id.partner_id.email,
            })
            if "errors" in data:
                msg = "\n".join(
                    ["A integração com IUGU retornou os seguintes erros"] +
                    ["%s" % data['errors']])
                raise UserError(msg)
            self.move_line_id.write({
                'date_maturity': self.date_change,
                'iugu_id': data['id'],
                'iugu_secure_payment_url': data['secure_url'],
                'iugu_digitable_line': data['bank_slip']['digitable_line'],
                'iugu_barcode_url': data['bank_slip']['barcode'],
            })
