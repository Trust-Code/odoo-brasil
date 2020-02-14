# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class L10nBrPaymentMode(models.Model):
    _inherit = 'l10n_br.payment.mode'

    receive_by_iugu = fields.Boolean(string="Receber pelo IUGU?")

    @api.constrains('receive_by_iugu', 'journal_id')
    def check_iugu_validation(self):
        for item in self:
            if item.receive_by_iugu and not item.journal_id:
                raise ValidationError(
                    'O preenchimento do diário é obrigatório para \
                    recebimento pelo IUGU')
