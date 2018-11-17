# © 2018 Carlos R. Silveira, ATSti
# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    natureza_operacao = fields.Char('Natureza Operação')
