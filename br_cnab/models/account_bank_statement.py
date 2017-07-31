# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    nosso_numero = fields.Char(string=u"Nosso Número", size=30)

    def _get_nosso_numero(self, bank, nosso_numero):
        # TODO Quando outros bancos modificar aqui
        if bank == '237':  # Bradesco
            return int(nosso_numero[8:19])
        elif bank == '756':
            return int(nosso_numero[:9])
        return nosso_numero

    @api.model
    def create(self, vals):
        if "nosso_numero" in vals:
            import ipdb; ipdb.set_trace()
            vals["nosso_numero"] = self._get_nosso_numero(vals["nosso_numero"])
        return super(AccountBankStatementLine, self).create(vals)

    def get_reconciliation_proposition(self, excluded_ids=None):
        res = super(AccountBankStatementLine, self).\
            get_reconciliation_proposition(excluded_ids)

        if self.nosso_numero:
            moves = self.env['account.move.line'].search(
                [('nosso_numero', '=', self.nosso_numero)])
            if moves:
                return moves
        return res
