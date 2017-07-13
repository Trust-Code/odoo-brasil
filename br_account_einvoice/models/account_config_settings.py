# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    nfe_email_template = fields.Many2one(
        'mail.template', string="Template de Email para NFe",
        domain=[('model_id.model', '=', 'account.invoice')])

    issue_eletronic_doc = fields.Selection([('o', u'Open'), ('p', u'Paid')],
                                  string=u'Emitir documento eletrônico',
                                  default='o',
                                  required=True,
                                  help=u'This field tells when to issue NFSe')

    def get_default_issue_eletronic_doc(self, fields):
        return {'issue_eletronic_doc':
                    self.env.user.company_id.issue_eletronic_doc}

    @api.multi
    def set_default_issue_eletronic_doc(self):
        self.env.user.company_id.issue_eletronic_doc = self.issue_eletronic_doc

    def get_default_nfe_email_template(self, fields):
        return {'nfe_email_template':
                    self.env.user.company_id.nfe_email_template.id}

    @api.multi
    def set_default_nfe_email_template(self):
        self.env.user.company_id.nfe_email_template = self.nfe_email_template
