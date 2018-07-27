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

    def get_opration_code(self):
        if self.payment_mode_id.payment_type == '01':
            return '018'
        elif self.payment_mode_id.payment_type == '02':
            return '700'

    def action_generate_payment_order_line(self):
        order_name = self.env['ir.sequence'].next_by_code('payment.order')
        payment_order = self.env['payment.order'].search([
            ('state', '=', 'draft'),
            ('payment_mode_id', '=', self.payment_mode_id.id),
            ('type', '=', 'payable')], limit=1)
        if not payment_order:
            payment_order = payment_order.create({
                'name': '%s' % order_name,
                'user_id': self.write_uid.id,
                'payment_mode_id': self.payment_mode_id.id,
                'state': 'draft',
                'type': 'payable',
                'currency_id': self.currency_id.id,
            })

        information_id = self.env['l10n_br.payment_information'].create({
            'payment_type': self.payment_mode_id.payment_type,
            'finality_ted': self.payment_mode_id.finality_ted,
            'mov_finality': self.payment_mode_id.mov_finality,
            'operation_code': self.get_opration_code(),
        })
        self.env['payment.order.line'].create({
            'partner_id': self.partner_id.id,
            'payment_order_id': payment_order.id,
            'payment_mode_id': self.payment_mode_id.id,
            'date_maturity': self.date_due,
            'value': self.amount,
            'name': self.number,
            'bank_account_id': self.bank_account_id.id,
            'move_id': self.move_id.id,
            'voucher_id': self.id,
            'payment_information_id': information_id.id,
            'nosso_numero': self.payment_mode_id.nosso_numero_sequence
            .next_by_id()
        })

    @api.multi
    def proforma_voucher(self):
        # TODO Validate before call super
        res = super(AccountVoucher, self).proforma_voucher()
        for item in self:
            item.action_generate_payment_order_line()
        return res

    def validade_doc_ted_fields(self):
        if not self.date_due:
            raise UserError(_("Please select a Due Date for the payment"))
        if datetime.strptime(self.date_due, DATE_FORMAT) < datetime.now():
            raise UserError(_("Due Date must be a future date"))

    @api.multi
    def write(self, vals):
        res = super(AccountVoucher, self).write(vals)
        if self.payment_mode_id.payment_type in ('01, 02'):
            self.validade_doc_ted_fields()
        return res
