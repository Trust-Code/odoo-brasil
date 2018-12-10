# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class l10nBrPaymentCnabImport(models.TransientModel):
    _name = 'l10n_br.payment.cnab.import'

    cnab_type = fields.Selection(
        [('receivable', 'Recebíveis'), ('payable', 'Pagáveis')])
    cnab_file = fields.Binary(
        string='Arquivo', help='Arquivo de retorno do tipo CNAB 240')

    journal_id = fields.Many2one(
        'account.journal', string="Diário Contábil",
        domain=[('type', '=', 'bank')],
        help="Diário Contábil a ser utilizado na importação do CNAB.")

    def validate_journal(self, acc_number, bra_number):
        account = self.journal_id.bank_account_id
        if acc_number != int(account.acc_number):
            raise UserError(
                'A conta não é a mesma do extrato.\nDiário: %s\nExtrato: %s' %
                (int(account.acc_number), acc_number))
        if bra_number != int(account.bra_number):
            raise UserError(
                'A agência não é a mesma do extrato: %s' %
                bra_number)

    def _get_account(self, cnab_file):
        return 0, 0

    def do_import(self, cnab_file):
        pass

    def action_import_cnab(self):
        try:
            cnab = base64.decodestring(self.cnab_file)
            acc_number, bra_number = self._get_account(cnab)

            self.validate_journal(acc_number, bra_number)
            return self.do_import(cnab)
        except UserError:
            raise
        except Exception as e:
            _logger.error(str(e), exc_info=True)
            msg = 'O arquivo importado não parece ser o correto:\n%s' % str(e)
            raise UserError(msg)
