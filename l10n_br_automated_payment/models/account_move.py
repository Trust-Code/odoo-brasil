# © 2019 Danimar Ribeiro
# Part of OdooNext. See LICENSE file for full copyright and licensing details.

import re
import iugu
from datetime import date
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.depends('line_ids')
    def _compute_receivables(self):
        self.receivable_move_line_ids = self.line_ids.filtered(
            lambda m: m.account_id.user_type_id.type == 'receivable'
        ).sorted(key=lambda m: m.date_maturity)

    @api.depends('line_ids')
    def _compute_payables(self):
        self.payable_move_line_ids = self.line_ids.filtered(
            lambda m: m.account_id.user_type_id.type == 'payable')
        
    receivable_move_line_ids = fields.Many2many(
        'account.move.line', string='Receivable Move Lines',
        compute='_compute_receivables')

    payable_move_line_ids = fields.Many2many(
        'account.move.line', string='Payable Move Lines',
        compute='_compute_payables')

    payment_journal_id = fields.Many2one(
        'account.journal', string='Forma de pagamento')

    def validate_data_iugu(self):
        errors = []
        for invoice in self:
            if not invoice.payment_journal_id.receive_by_iugu:
                continue
            partner = invoice.partner_id.commercial_partner_id
            if not self.env.user.company_id.iugu_api_token:
                errors.append('Configure o token de API')
            if partner.is_company and not partner.legal_name:
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

    def send_information_to_iugu(self):
        for invoice in self:
            if not invoice.payment_journal_id.receive_by_iugu:
                continue
                  
            token = self.env.user.company_id.iugu_api_token
            url_base = self.env.user.company_id.iugu_url_base
            iugu.config(token=token)
            iugu_invoice_api = iugu.Invoice()

            for moveline in invoice.receivable_move_line_ids:
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

    def action_post(self):
        self.validate_data_iugu()
        result = super(AccountMove, self).action_post()
        self.send_information_to_iugu()
        return result


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
