# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    nfe_email_template = fields.Many2one(
        'mail.template', string="Template de Email para NFe")
    issue_eletronic_doc = fields.Selection([('o', u'Open'), ('p', u'Paid')],
                                  default='o',
                                  required=True,
                                  help=u'This field tells when to issue NFSe')
