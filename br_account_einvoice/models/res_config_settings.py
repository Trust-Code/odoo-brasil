# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nfe_email_template = fields.Many2one(
        'mail.template', string="Template de Email para NFe",
        domain=[('model_id.model', '=', 'account.invoice')])

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['nfe_email_template'] = self.env.user.company_id\
            .nfe_email_template.id
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.nfe_email_template = self.nfe_email_template
