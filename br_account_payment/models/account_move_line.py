# -*- coding: utf-8 -*- © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
import datetime


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line','mail.thread']

    payment_mode_id = fields.Many2one(
        'payment.mode', string=u"Modo de pagamento")
    overdue = fields.Boolean(compute="_compute_overdue", store=True,
                             string="Pagamento Atrasado")

    billing_line = fields.Boolean(compute="_compute_billing", store=True,
                                  string="Linha de Cobrança")
    billing_type = fields.Selection([('1',u'A Receber'),('2',u'A Pagar')],store=True,
                                    compute="_compute_billing")

    billing_status = fields.Selection([('open',u'Em Aberto'),('partially',u'Parcialmente Pago'),
                                       ('overdue',u'Título em Atraso'),('pay',u'Pago')],
                                      compute='_compute_billing_status', store=True,track_visibility='onchange')
    total_quota_invoice = fields.Char(compute="_compute_all_quotas", size=2)

    @api.depends('invoice_id')
    def _compute_all_quotas(self):
        for record in self:
            if record.billing_type == '1':
                record.total_quota_invoice = "%02d" %(len(record.invoice_id.receivable_move_line_ids))
            if record.billing_type == '2':
                record.total_quota_invoice = "%02d" %(len(record.invoice_id.payable_move_line_ids))

    @api.depends('billing_status','billing_type','billing_line','matched_credit_ids',
                 'date_maturity','matched_debit_ids','reconciled')
    def _compute_billing_status(self):
        date_now = datetime.datetime.now().strftime('%Y-%m-%d')
        for record in self:
            if record.billing_line:
                record.billing_status = 'open'
                if record.date_maturity < date_now and record.reconciled == False:
                    record.billing_status = 'overdue'
                if record.billing_type == '1' and record.matched_credit_ids:
                    record.billing_status = 'partially'
                if record.billing_line == '2' and record.matched_debit_ids:
                    record.billing_status = 'partially'
                if record.reconciled:
                    record.billing_status = 'pay'


    @api.depends('user_type_id','debit','credit','billing_line','billing_type')
    def _compute_billing(self):
        for record in self:
            #Títulos a Receber
            if record.user_type_id.type == 'payable' and record.debit == 0:
                record.billing_line = True
                record.billing_type = '2'
            #Títulos a Pagar
            elif record.user_type_id.type == 'receivable' and record.credit == 0:
                record.billing_line = True
                record.billing_type = '1'
            else:
                record.billing_line = False

    @api.multi
    @api.depends('debit', 'credit', 'user_type_id', 'amount_residual')
    def _compute_payment_value(self):
        for item in self:
            item.payment_value = item.debit \
                if item.user_type_id.type == 'receivable' else item.credit * -1
    payment_value = fields.Monetary(
        string="Valor", compute=_compute_payment_value, store=True,
        currency_field='company_currency_id')

    @api.multi
    def action_register_payment(self):
        dummy, act_id = self.env['ir.model.data'].get_object_reference(
            'account', 'action_account_invoice_payment')
        receivable = (self.user_type_id.type == 'receivable')
        vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
        vals['context'] = {
            'default_amount': self.debit or self.credit,
            'default_partner_type': 'customer' if receivable else 'supplier',
            'default_partner_id': self.partner_id.id,
            'default_communication': self.name,
            'default_payment_type': 'inbound' if receivable else 'outbound',
            'default_move_line_id': self.id,
        }
        if self.invoice_id:
            vals['context']['default_invoice_ids'] = [self.invoice_id.id]
        return vals


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"
    payment_mode_id = fields.Many2one('payment.mode', string=u"Modo de pagamento", readonly=True)

    @api.model
    def create(self, vals):
        aml = []
        if vals.get('debit_move_id', False):
            aml.append(vals['debit_move_id'])
        if vals.get('credit_move_id', False):
            aml.append(vals['credit_move_id'])
        # Get value of matched percentage from both move before reconciliating
        lines = self.env['account.move.line'].browse(aml)
        if lines[0].payment_mode_id:
            vals['payment_mode_id'] = lines[0].payment_mode_id.id
        res = super(AccountPartialReconcile, self).create(vals)

        return res


        res.update('')