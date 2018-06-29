# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


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

    def action_generate_payment_order_line(self):
        order_name = self.env['ir.sequence'].next_by_code('payment.order')
        payment_order = self.env['payment.order'].search([
            ('state', '=', 'draft'),
            ('payment_mode_id', '=', self.payment_mode_id.id),
            ('type', '=', 'payable')], limit=1)
        order_dict = {
            'name': u'%s' % order_name,
            'user_id': self.write_uid.id,
            'payment_mode_id': self.payment_mode_id.id,
            'state': 'draft',
            'type': 'payable',
            'currency_id': self.currency_id.id,
        }
        if not payment_order:
            payment_order = payment_order.create(order_dict)

        information_id = self.env['l10n_br.payment_information'].create({
            'payment_type': self.payment_mode_id.payment_type,
            'mov_finality': '01',  # Crédito em Conta Corrente
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
        })

    @api.multi
    def proforma_voucher(self):
        # TODO Validate before call super
        res = super(AccountVoucher, self).proforma_voucher()
        for item in self:
            item.action_generate_payment_order_line()
        return res
