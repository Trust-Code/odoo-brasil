# © 2019 Danimar Ribeiro
# Part of OdooNext. See LICENSE file for full copyright and licensing details.



from odoo import api, fields, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    transaction_url = fields.Char(string="Url de Pagamento", size=256) 
    origin_move_line_id = fields.Many2one('account.move.line')
    date_maturity = fields.Date(string="Data de Vencimento")

    def action_wizard_edit(self):
        pass

    def action_verify_transaction(self):
        pass

    def action_cancel_transaction(self):
        pass