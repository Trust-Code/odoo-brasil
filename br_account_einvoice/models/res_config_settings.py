# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nfe_email_template = fields.Many2one(
        'mail.template', string="Template de Email para NFe",
        domain=[('model_id.model', '=', 'account.invoice')])

    def get_default_nfe_email_template(self, fields):
        return {'nfe_email_template':
                self.env.user.company_id.nfe_email_template.id}

    @api.multi
    def set_default_nfe_email_template(self):
        self.env.user.company_id.nfe_email_template = self.nfe_email_template
