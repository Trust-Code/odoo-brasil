# © 2019 Mackilem, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', "Modo de Pagamento",
        attrs="{'readonly': [('state', 'in', ['done', 'cancel'])]}")
    payment_type = fields.Selection(
        related='payment_mode_id.payment_type', readonly=True)
    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência")
    date_payment = fields.Date(string="Payment Date", )

    def get_order_line(self):
        for line in self.move_id.line_ids:
            if (line.l10n_br_order_line_id.autenticacao_pagamento):
                return line.l10n_br_order_line_id

    @api.onchange('payment_mode_id')
    def _onchange_payment_mode_id(self):
        self.payment_type = self.payment_mode_id.payment_type

    @api.onchange('employee_id')
    def _onchange_payment_cnab_employee_id(self):
        if self.employee_id:
            self.bank_account_id = self.employee_id.bank_account_id.id

    def _prepare_payment_order_vals(self):
        address_account_id = self.address_id.property_account_payable_id
        move_line_id = self.account_move_id.line_ids.filtered(
            lambda x: x.account_id == address_account_id)
        return {
            'partner_id': self.address_id.id,
            'amount_total': self.total_amount,
            'name': self.name,
            'bank_account_id': self.bank_account_id.id,
            'partner_acc_number': self.bank_account_id.acc_number,
            'partner_bra_number': self.bank_account_id.bra_number,
            'move_line_id': move_line_id.id,
            'expense_sheet_id': self.id,
            'date_maturity': self.date_payment,
            'invoice_date': self.accounting_date,
        }

    @api.multi
    def action_sheet_move_create(self):
        if self.payment_mode != 'own_account':
            return super(HrExpenseSheet, self).action_sheet_move_create()

        for item in self:
            if item.payment_mode_id and item.payment_mode_id.type == 'payable':
                item.validate_cnab_fields()
        res = super(HrExpenseSheet, self).action_sheet_move_create()
        for item in self:
            order_line_obj = self.env['payment.order.line']
            if item.payment_mode_id:
                order_line_obj.action_generate_payment_order_line(
                    item.payment_mode_id,
                    item._prepare_payment_order_vals())
        return res

    def validate_cnab_fields(self):
        if not self.date_payment:
            raise UserError(_("Please select a Payment Date"))
