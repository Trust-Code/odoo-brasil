

from odoo import fields, models


class WizardChangePayment(models.TransientModel):
    _name = 'wizard.change.payment'

    move_line_id = fields.Many2one('account.move.line', readonly=True)
    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string="Modo de Pagamento")
    payment_type = fields.Selection(
        related="payment_mode_id.payment_type")
    barcode = fields.Char(string="Código de barras")
    partner_id = fields.Many2one(
        'res.partner', readonly=True, string="Parceiro")
    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência",
        domain="[('partner_id', '=', partner_id)]")
    date_maturity = fields.Date(string="Data de Vencimento")
