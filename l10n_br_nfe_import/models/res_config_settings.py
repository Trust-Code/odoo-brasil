from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_sequence_id = fields.Many2one(
        'ir.sequence', string="Sequência para código de produto")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            product_sequence_id=int(params.get_param(
                'br_nfe_import.product_sequence', default=0))
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'br_nfe_import.product_sequence', self.product_sequence_id.id)
