# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    boleto_email_tmpl = fields.Many2one(
        'mail.template', string="Template de Email para Envio de Boleto",
        domain=[('model_id.model', '=', 'account.invoice')])

    def get_default_boleto_email_tmpl(self, fields):
        return {'boleto_email_tmpl':
                self.env.user.company_id.boleto_email_tmpl.id}

    @api.multi
    def set_default_boleto_email_tmpl(self):
        self.env.user.company_id.boleto_email_tmpl = self.boleto_email_tmpl
