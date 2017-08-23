# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    nosso_numero = fields.Char(string=u"Nosso Número", size=30)

    def get_reconciliation_proposition(self, excluded_ids=None):
        res = super(AccountBankStatementLine, self).\
            get_reconciliation_proposition(excluded_ids)
        if self.nosso_numero:
            moves = self.env['account.move.line'].search(
                [('nosso_numero', '=', self.nosso_numero)])
            if moves:
                return moves
        return res
