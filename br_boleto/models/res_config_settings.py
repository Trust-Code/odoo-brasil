# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    boleto_email_tmpl = fields.Many2one(
        'mail.template', string="Template de Email para Envio de Boleto",
        domain=[('model_id.model', '=', 'account.invoice')])

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['boleto_email_tmpl'] = self.env.user.company_id\
            .boleto_email_tmpl.id
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.boleto_email_tmpl = self.boleto_email_tmpl
