# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import iugu
from datetime import date
from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    iugu_status = fields.Char(string="Status Iugu", default='pending')
    iugu_id = fields.Char(string="ID Iugu", size=60)
    iugu_secure_payment_url = fields.Char(string="URL de Pagamento", size=500)
    iugu_digitable_line = fields.Char(string="Linha Digitável", size=100)
    iugu_barcode_url = fields.Char(string="Código de barras", size=100)

    # TODO Ler a fatura no IUGU e verificar se teve juros.
    def action_mark_paid_iugu(self):
        self.ensure_one()
        ref = 'Fatura Ref: %s - %s' % (self.move_id.name, self.name)
        journal = self.payment_mode_id.journal_id
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': journal.id,
            'company_id': journal.company_id.id,
            'date': date.today(),
            'ref': ref,
        })
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        counterpart_aml_dict = {
            'name': ref,
            'move_id': move.id,
            'partner_id': self.partner_id.id,
            'debit': 0.0,
            'credit': self.amount_residual,
            'currency_id': self.currency_id.id,
            'account_id': self.account_id.id,
        }
        liquidity_aml_dict = {
            'name': ref,
            'move_id': move.id,
            'partner_id': self.partner_id.id,
            'debit': self.amount_residual,
            'credit': 0.0,
            'currency_id': self.currency_id.id,
            'account_id': journal.default_debit_account_id.id,
        }

        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        aml_obj.create(liquidity_aml_dict)
        move.post()
        (counterpart_aml + self).reconcile()
        return move

    def action_notify_due_payment(self):
        if self.invoice_id:
            self.invoice_id.message_post(
                body='Notificação do IUGU: Fatura atrasada')

    def action_verify_iugu_payment(self):
        if self.iugu_id:
            token = self.env.user.company_id.iugu_api_token
            iugu.config(token=token)
            iugu_invoice_api = iugu.Invoice()

            data = iugu_invoice_api.search(self.iugu_id)
            if "errors" in data:
                raise UserError(data['errors'])
            if data.get('status', '') == 'paid' and not self.reconciled:
                self.iugu_status = data['status']
                self.action_mark_paid_iugu()
            else:
                self.iugu_status = data['status']
        else:
            raise UserError('Esta parcela não foi enviada ao IUGU')

    def action_cancel_iugu(self):
        if not self.iugu_id:
            raise UserError('Esta parcela não foi enviada ao IUGU')
        token = self.env.user.company_id.iugu_api_token
        iugu.config(token=token)
        iugu_invoice_api = iugu.Invoice()
        iugu_invoice_api.cancel(self.iugu_id)
        self.iugu_status = 'canceled'

    @api.multi
    def unlink(self):
        for line in self:
            if line.iugu_id:
                token = self.env.user.company_id.iugu_api_token
                iugu.config(token=token)
                iugu_invoice_api = iugu.Invoice()
                iugu_invoice_api.cancel(line.iugu_id)
        return super(AccountMoveLine, self).unlink()

    def open_wizard_change_date(self):
        return({
            'name': 'Alterar data de vencimento',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.change.iugu.invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_line_id': self.id,
            }
        })
