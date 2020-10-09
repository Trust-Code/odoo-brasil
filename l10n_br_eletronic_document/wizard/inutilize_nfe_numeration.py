from odoo import fields, models


class InutilizationNFeNumeration(models.TransientModel):
    _name = 'wizard.inutilization.nfe.numeration'
    _description = "Inutilização numeração NF-e"

    numeration_start = fields.Integer('Começo da Numeração', required=True)
    numeration_end = fields.Integer('Fim da Numeração', required=True)
    serie = fields.Char(string='Série', required=True)
    modelo = fields.Selection([
        ('55', '55 - NFe'),
        ('65', '65 - NFCe'), ],
        string=u'Modelo', required=True)
    justificativa = fields.Text(
        u'Justificativa', required=True,
        help=u'Mínimo: 15 caracteres;\nMáximo: 255 caracteres.')

    def action_inutilize_nfe(self):
        name = u'Série Inutilizada {inicio} - {fim}'.format(
            inicio=self.numeration_start, fim=self.numeration_end
        )
        inut_inv = self.env['invoice.eletronic.inutilized'].create(dict(
            name=name,
            numeration_start=self.numeration_start,
            numeration_end=self.numeration_end,
            justificativa=self.justificativa,
            modelo=self.modelo,
            serie=self.serie,
            state='error',
        ))
        return inut_inv.action_send_inutilization()
