# © 2019 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_br_serie_supplier = fields.Char(string="Supplier Series", size=6)
    l10n_br_sped_emit = fields.Selection(
        [('0', '0 - Emissão própria'),
         ('1', '1 - Terceiros')], string="Issuer")
    l10n_br_nfe_key = fields.Char(string="NFe Key", size=60)
