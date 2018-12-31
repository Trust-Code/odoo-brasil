# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class L10nBrPaymentStatementLine(models.Model):
    _inherit = 'l10n_br.payment.statement.line'

    amount_fee = fields.Float(string="Juros/Multa")
    original_amount = fields.Float(string="Valor Título")
    discount = fields.Float(string="Desconto")
    bank_fee = fields.Float(string="Valor Tarifas")
