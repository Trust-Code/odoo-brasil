# -*- coding: utf-8 -*-
# © 2016 Alessandro Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class InutilizationNFeNumeration(models.TransientModel):
    _name = 'wizard.inutilization.nfe.numeration'

    numeration_start = fields.Integer('Começo da Numeração', required=True)
    numeration_end = fields.Integer('Fim da Numeração', required=True)

    @api.multi
    def action_inutilize_nfe(self):
        if self.numeration_start > self.numeration_end:
            raise UserError('O Começo da Numeração deve ser menor que o Fim '
                            'da Numeração')
        inutilized_serie = range(self.numeration_start,
                                 self.numeration_end + 1)
        docs = self.env['invoice.eletronic'].search([(
            'numero', 'in', inutilized_serie)])
        if docs:
            raise UserError('Não é possível cancelar essa série pois já '
                            'existem documentos com essa numeração.')
        for number in inutilized_serie:
            self.env['invoice.eletronic.inutilized'].create(
                dict(numero=number))
