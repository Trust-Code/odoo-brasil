# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from datetime import datetime
from odoo import api, fields, models
from ..bancos.sicoob import Sicoob240


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    def action_generate_payable_cnab(self):
        self.file_number = self.env['ir.sequence'].next_by_code('cnab.nsa')
        self.data_emissao_cnab = datetime.now()
        cnab = self.select_bank_cnab()[str(
            self.payment_mode_id.bank_account_id.bank_id.bic)]
        cnab.create_cnab(self.line_ids)
        self.cnab_file = base64.b64encode(cnab.write_cnab())
        self.name = 'cnab_pagamento.rem'

    def select_bank_cnab(self):
        return {
                    '756': Sicoob240(self),
                    # '033': Santander240(self),
                    # '641': Itau240(self),
                    # '237': Bradesco240(self)
                }

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, ondelete='restrict',
        default=lambda self: self.env['res.company']._company_default_get(
            'account.payment.mode'))


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    voucher_id = fields.Many2one('account.voucher', "Recibo Origem")
    payment_information_id = fields.Many2one(
        'l10n_br.payment_information', string="Payment Information")

    @api.depends('payment_information_id')
    def calc_final_value(self):
        for item in self:
            payment = item.payment_information_id
            desconto = payment.rebate_value + payment.discount_value
            acrescimo = payment.duty_value + payment.mora_value
            item.value_final = (item.value - desconto + acrescimo)

    value_final = fields.Float(
        string="Final Value", compute="calc_final_value",
        digits=(18, 2), readonly=True)

    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência")
