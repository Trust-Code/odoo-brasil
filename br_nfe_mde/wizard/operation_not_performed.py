# -*- coding: utf-8 -*-
# © 2017 Fábio Luna <fabiocluna@hotmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class OperationNotPerformed(models.TransientModel):
    _name = 'wizard.operation.not.perfomed'

    mde_id = fields.Many2one('nfe.mde', string="Documento")
    justificativa = fields.Text('Justificativa', size=255, required=True)

    @api.multi
    def action_operation_not_performed(self):
        if self.mde_id and len(self.justificativa) > 15:
            self.mde_id.action_not_operation(
                justificativa=self.justificativa)
        else:
            raise UserError(u"Justificativa deve ter mais de 15 caracteres")
