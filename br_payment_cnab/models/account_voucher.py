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

    barcode = fields.Char('Barcode')

    interest_value = fields.Float('Interest Value')

    fine_value = fields.Float('Fine Value')

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
            'value': self.amount - self.fine_value - self.interest_value,
            'name': self.number,
            'bank_account_id': self.bank_account_id.id,
            'move_id': self.move_id.id,
            'voucher': self.id,
            'date_maturity': self.date_due,
            'invoice_date': self.date,
            'barcode': self.barcode,
            'fine_value': self.fine_value,
            'interest_value': self.interest_value,
        }

    @api.multi
    def proforma_voucher(self):
        # TODO Validate before call super
        res = super(AccountVoucher, self).proforma_voucher()
        for item in self:
            self.env['payment.order.line'].action_generate_payment_order_line(
                self.payment_mode_id, **self._prepare_payment_order_vals())
        return res

    def validade_cnab_fields(self):
        if not self.date_due:
            raise UserError(_("Please select a Due Date for the payment"))
        if datetime.strptime(self.date_due, DATE_FORMAT) < datetime.now():
            raise UserError(_("Due Date must be a future date"))

    def create_interest_fine_line(self, line_type, vals):
        account_id = self.env['ir.config_parameter'].sudo().get_param(
            'br_payment_cnab.{}_account_id'.format(line_type))
        if not account_id:
            raise UserError(_(
                "Please configure the interest and fine accounts"))
        line_vals = (0, 0, {
            'name': _('Fine Line') if line_type == 'fine' else _(
                'Interest Line'),
            'quantity': 1,
            'price_unit': vals.get('{}_value'.format(line_type)),
            'account_id': account_id
        })
        if vals.get('line_ids'):
            vals['line_ids'].append(line_vals)
        else:
            vals.update(line_ids=[line_vals])
        return vals

    @api.multi
    def write(self, vals):
        if vals.get('interest_value'):
            vals = self.create_interest_fine_line('interest', vals)
        if vals.get('fine_value'):
            vals = self.create_interest_fine_line('fine', vals)
        res = super(AccountVoucher, self).write(vals)
        if self.payment_mode_id and\
                self.payment_mode_id.payment_type in ('01, 02', '06', '07'):
            self.validade_cnab_fields()
        return res

    @api.model
    def create(self, vals):
        if vals.get('interest_value', 0) > 0:
            vals = self.create_interest_fine_line('interest', vals)
        if vals.get('fine_value', 0) > 0:
            vals = self.create_interest_fine_line('fine', vals)
        return super(AccountVoucher, self).create(vals)
