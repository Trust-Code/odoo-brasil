# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_br_sequence_nosso_numero = fields.Many2one(
        'ir.sequence', string="Sequência Nosso Número")

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
