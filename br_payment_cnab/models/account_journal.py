# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def wizard_import_bank_payments_cnab(self):
        action = self.env.ref(
            'br_payment_cnab.action_import_bank_payments_cnab')
        return {
            'name': action.name,
            'context': dict(
                self.env.context,
                journal_id=self.id),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_br.payment.cnab.import',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
