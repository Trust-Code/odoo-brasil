# © 2019 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_purchase_fiscal_position_id = fields.Many2one(
        string="Purchase Fiscal Position",
        comodel_name="account.fiscal.position",
        domain="[('fiscal_type', '=', 'entrada')]",
        company_dependent=True,
        ondelete="set null")
