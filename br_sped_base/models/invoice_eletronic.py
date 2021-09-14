# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    emissao_doc = fields.Selection(
        [('0', '0 - Emissão própria'),
         ('1', '1 - Terceiros')], u'Indicador do Emitente', readonly=True,
        required=False, default='0')


class InvoiceEletronicItem(models.Model):
    _inherit = "invoice.eletronic.item"

    # na importacao xml de entrada, carregar o valor neste campo
    num_item = fields.Integer(
        string=u"Sequêncial Item", default=1, readonly=True)

