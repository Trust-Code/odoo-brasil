# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    nfe_email_template = fields.Many2one(
        'mail.template', string="Template de Email para NFe",
        domain=[('model_id.model', '=', 'account.invoice')])

    def get_default_nfe_email_template(self, fields):
        mail = self.env['mail.template'].search(
            [('model_id.model', '=', 'account.invoice')])
        return {'nfe_email_template': mail.id}

    @api.multi
    def set_account_bool(self):
        self.env.user.company_id.nfe_email_template = self.nfe_email_template
