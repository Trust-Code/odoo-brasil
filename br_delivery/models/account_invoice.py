# -*- coding: utf-8 -*-
# © 2010  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    carrier_id = fields.Many2one(
        'delivery.carrier', 'Transportadora', readonly=True,
        states={'draft': [('readonly', False)]})
    vehicle_id = fields.Many2one(
        'br_delivery.carrier.vehicle', u'Veículo', readonly=True,
        states={'draft': [('readonly', False)]})
    incoterm = fields.Many2one(
        'stock.incoterms', 'Tipo do Frete', readonly=True,
        states={'draft': [('readonly', False)]},
        help="Incoterm which stands for 'International Commercial terms' "
        "implies its a series of sales terms which are used in the "
        "commercial transaction.")

    #TODO Deve herdar invoice eletronic para fazer esta validação
    @api.multi
    def _hook_validation(self):
        result = super(AccountInvoice, self).nfe_check(cr, uid, ids, context)
        strErro = u''

        for inv in self.browse(cr, uid, ids, context=context):
            # Carrier
            if inv.carrier_id:

                if not inv.carrier_id.partner_id.legal_name:
                    strErro = u'Transportadora - Razão Social\n'

                if not inv.carrier_id.partner_id.cnpj_cpf:
                    strErro = 'Transportadora - CNPJ/CPF\n'

            # Carrier Vehicle
            if inv.vehicle_id:

                if not inv.vehicle_id.plate:
                    strErro = u'Transportadora / Veículo - Placa\n'

                if not inv.vehicle_id.state_id.code:
                    strErro = u'Transportadora / Veículo - UF da Placa\n'

                if not inv.vehicle_id.rntc_code:
                    strErro = u'Transportadora / Veículo - RNTC\n'

        if strErro:
            raise UserError(
                _(u"Validação da Nota fiscal:\n '%s'") % (strErro))

        return result
