# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountClose(models.TransientModel):
    _name = 'account.close.wizard'

    start_date = fields.Date(string="Inicio")
    end_date = fields.Date(string="Final")

    @api.multi
    def action_close_period(self):
        pass
