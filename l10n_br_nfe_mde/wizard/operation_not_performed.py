from odoo import api, fields, models
from odoo.exceptions import UserError


class OperationNotPerformed(models.TransientModel):
    _name = 'wizard.operation.not.perfomed'
    _description = "Wizard Operacao nao Confirmada"

    mde_id = fields.Many2one('nfe.mde', string="Documento")
    justificativa = fields.Text('Justificativa', required=True)

    def action_operation_not_performed(self):
        if self.mde_id and len(self.justificativa) > 15:
            self.mde_id.action_not_operation(
                justificativa=self.justificativa)
        else:
            raise UserError(u"Justificativa deve ter mais de 15 caracteres")
