# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class BrBoletoWizard(models.TransientModel):
    _name = 'br.boleto.wizard'

    date_change = fields.Date(string='Alterar Vencimento')
    invoice_id = fields.Many2one('account.invoice', readonly=1)

    @api.multi
    def imprimir_boleto(self):
        return self.env['report'].get_action([self.invoice_id.id],
                                             'br_boleto.report.print')
