# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    payment_mode_id = fields.Many2one('payment.mode', "Modo de Pagamento")
    payment_type = fields.Selection(
        [('01', 'TED - Transferência Bancária'),
         ('02', 'DOC - Transferência Bancária'),
         ('03', 'Pagamento de Títulos'),
         ('04', 'Tributos com código de barras'),
         ('05', 'GPS - Guia de previdencia Social'),
         ('06', 'DARF Normal'),
         ('07', 'DARF Simples'),
         ('08', 'FGTS')],
        string="Tipo de Operação")
    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência",
        domain="[('partner_id', '=', partner_id)]")

    @api.onchange('payment_mode_id')
    def _onchange_payment_mode_id(self):
        self.payment_type = self.payment_mode_id.payment_type

    @api.onchange('partner_id')
    def _onchange_payment_cnab_partner_id(self):
        bnk_account_id = self.env['res.partner.bank'].search(
            [('partner_id', '=', self.partner_id.commercial_partner_id.id)],
            limit=1)
        self.bank_account_id = bnk_account_id.id

    def _prepare_payment_order_vals(self):
        return {
            'partner_id': self.partner_id.id,
            'value': self.amount,
            'name': self.number,
            'bank_account_id': self.bank_account_id.id,
            'move_id': self.move_id.id,
            'voucher': self.id,
            'date_maturity': self.date_due,
            'invoice_date': self.date,
        }

    @api.multi
    def proforma_voucher(self):
        # TODO Validate before call super
        res = super(AccountVoucher, self).proforma_voucher()
        for item in self:
            self.env['payment.order.line'].action_generate_payment_order_line(
                self.payment_mode_id, **self._prepare_payment_order_vals())
        return res

    def validade_doc_ted_fields(self):
        if not self.date_due:
            raise UserError(_("Please select a Due Date for the payment"))
        if datetime.strptime(self.date_due, DATE_FORMAT) < datetime.now():
            raise UserError(_("Due Date must be a future date"))

    @api.multi
    def write(self, vals):
        res = super(AccountVoucher, self).write(vals)
        if self.payment_mode_id and\
                self.payment_mode_id.payment_type in ('01, 02'):
            self.validade_doc_ted_fields()
        return res
