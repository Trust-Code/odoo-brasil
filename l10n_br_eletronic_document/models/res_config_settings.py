from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_br_nfe_email_template = fields.Many2one(
        'mail.template', string="Template de Email para NFe",
        domain=[('model_id.model', '=', 'account.move')])

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['l10n_br_nfe_email_template'] = self.env.user.company_id\
            .l10n_br_nfe_email_template.id
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.l10n_br_nfe_email_template = self.l10n_br_nfe_email_template
