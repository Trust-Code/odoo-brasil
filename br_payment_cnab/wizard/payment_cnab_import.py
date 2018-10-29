# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import base64
from io import StringIO

from odoo import fields, models

_logger = logging.getLogger(__name__)

try:
    from pycnab240.file import File
    from pycnab240.utils import get_bank, get_return_message
except ImportError:
    _logger.warning('Cannot import pycnab240')


class l10nBrPaymentCnabImport(models.TransientModel):
    _name = 'l10n_br.payment.cnab.import'

    cnab_file = fields.Binary(
        string='Arquivo', help='Arquivo de retorno do tipo CNAB 240')

    journal_id = fields.Many2one(
        'account.journal', string="Diário Contábil",
        domain=[('type', '=', 'bank')],
        help="Diário Contábil a ser utilizado na importação do CNAB.")

    cnab_preview = fields.Html(string='Resumo da importação', readonly=True)

    def import_cnab(self):
        cnab = base64.decodestring(self.cnab_file)
        stream = StringIO(cnab.decode('ascii'))

        bank = get_bank(self.journal_id.bank_id.bic)
        loaded_cnab = File(bank)
        loaded_cnab.load_return_file(stream)
        for lot in loaded_cnab.lots:
            for event in lot.events:
                message = get_return_message(self.journal_id.bank_id.bic,
                                             event.ocorrencias_retorno.strip())
                print("%s: %s - %s" % (event.numero_documento_cliente,
                                       event.ocorrencias_retorno, message))

        action = self.env.ref('br_payment_cnab.action_payment_statement_tree')
        return action.read()[0]
