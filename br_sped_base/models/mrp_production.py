# © 2019 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    l10n_production_start_date = fields.Date(string="Start Date")
    l10n_production_end_date = fields.Date(string="End Date")

    @api.multi
    def button_mark_done(self):
        # TODO Validar ordens de produção com cadastro correto apenas
        return super(MrpProduction, self).button_mark_done()
