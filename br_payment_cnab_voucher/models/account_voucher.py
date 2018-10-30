# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', "Modo de Pagamento")
    payment_type = fields.Selection(
        [('01', 'TED - Transferência Bancária'),
         ('02', 'DOC - Transferência Bancária'),
         ('03', 'Pagamento de Títulos'),
         ('04', 'Tributos com código de barras'),
         ('05', 'GPS - Guia de previdencia Social'),
         ('06', 'DARF Normal'),
         ('07', 'DARF Simples'),
         ('08', 'FGTS'),
         ('09', 'ICMS')],
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
        move_line_id = self.move_id.line_ids.filtered(
            lambda x: x.account_id == self.account_id)
        return {
            'partner_id': self.partner_id.id,
            'amount_total':
            self.amount - self.fine_value - self.interest_value,
            'name': self.number,
            'bank_account_id': self.bank_account_id.id,
            'move_line_id': move_line_id.id,
            'voucher_id': self.id,
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
            order_line_obj = self.env['payment.order.line']
            if item.payment_mode_id:
                order_line_obj.action_generate_payment_order_line(
                    item.payment_mode_id,
                    **item._prepare_payment_order_vals())
        return res

    def validate_cnab_fields(self):
        if not self.date_due:
            raise UserError(_("Please select a Due Date for the payment"))
        if fields.Date.from_string(self.date_due) < date.today():
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
        for item in self:
            if item.payment_mode_id and item.payment_mode_id.type == 'payable':
                item.validate_cnab_fields()
        return res

    @api.model
    def create(self, vals):
        if vals.get('interest_value', 0) > 0:
            vals = self.create_interest_fine_line('interest', vals)
        if vals.get('fine_value', 0) > 0:
            vals = self.create_interest_fine_line('fine', vals)
        res = super(AccountVoucher, self).create(vals)
        if res.payment_mode_id and res.payment_mode_id.type == 'payable':
            res.validate_cnab_fields()
        return res
