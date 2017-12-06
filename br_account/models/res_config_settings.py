# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2014  KMEE - www.kmee.com.br
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_simples_nacional = fields.Boolean(
        string='Simples Nacional',
        implied_group='br_account.group_simples_nacional')