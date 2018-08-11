# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    incoterm_id = fields.Many2one(
        'stock.incoterms', 'Tipo do Frete',
        help="Incoterm which stands for 'International "
        "Commercial terms' implies its a series "
        "of sales terms which are used in the "
        "commercial transaction.")
    carrier_id = fields.Many2one('delivery.carrier', 'Método de Entrega')

    @api.onchange('carrier_id')
    def _onchange_br_delivery_carrier_id(self):
        if self.carrier_id:
            self.incoterm_id = self.carrier_id.incoterm
            self.shipping_supplier_id = self.carrier_id.partner_id
            self.vehicle_rntc = self.carrier_id.antt_code

    @api.onchange('incoterm_id')
    def _onchange_br_delivery_incoterm(self):
        if self.incoterm_id:
            self.freight_responsibility = \
                self.incoterm_id.freight_responsibility
