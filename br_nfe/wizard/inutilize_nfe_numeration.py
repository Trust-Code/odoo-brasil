# -*- coding: utf-8 -*-
# © 2016 Alessandro Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class InutilizationNFeNumeration(models.TransientModel):
    _name = 'wizard.inutilization.nfe.numeration'

    numeration_start = fields.Integer('Começo da Numeração', required=True)
    numeration_end = fields.Integer('Fim da Numeração', required=True)
    serie = fields.Many2one('br_account.document.serie', string='Série',
                            required=True)
    modelo = fields.Selection([
        ('55', '55 - NFe'),
        ('65', '65 - NFCe'), ],
        string='Modelo', required=True)
    justificativa = fields.Text(
        'Justificativa', required=True,
        help='Mínimo: 15 caracteres;\nMáximo: 255 caracteres.')

    @api.multi
    def action_inutilize_nfe(self):
        name = 'Série Inutilizada {inicio} - {fim}'.format(
            inicio=self.numeration_start, fim=self.numeration_end
        )
        inut_inv = self.env['invoice.eletronic.inutilized'].create(dict(
            name=name,
            numeration_start=self.numeration_start,
            numeration_end=self.numeration_end,
            justificativa=self.justificativa,
            modelo=self.modelo,
            serie=self.serie.id,
            state='error',
        ))
        inut_inv.action_send_inutilization()
