# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

STATE = {'edit': [('readonly', False)]}


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    nfe_mde_id = fields.Many2one(
        'nfe.mde', string=u"Manifesto Eletrônico",
        readonly=True)


class InvoiceEletronicEvent(models.Model):
    _inherit = 'invoice.eletronic.event'

    nfe_mde_id = fields.Many2one(
        'nfe.mde', string=u"Manifesto Eletrônico",
        readonly=True, states=STATE)
