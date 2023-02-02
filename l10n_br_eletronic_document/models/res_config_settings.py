from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_br_nfe_email_template = fields.Many2one(
        'mail.template', string="Template de Email para NFe",
        related='company_id.l10n_br_nfe_email_template', readonly=False,
        domain=[('model_id.model', '=', 'account.move')])

    l10n_br_nfe_sequence = fields.Many2one(
        'ir.sequence', string="Sequência Numeracao NFe",
        related='company_id.l10n_br_nfe_sequence', readonly=False)

    l10n_br_nfe_service_sequence = fields.Many2one(
        'ir.sequence', string="Sequência Numeracao NFe de Serviço",
        related='company_id.l10n_br_nfe_service_sequence', readonly=False)

    l10n_br_automated_weight = fields.Boolean(
        string="Calculo de peso automatizado",
        related="company_id.l10n_br_automated_weight",
        readonly=False,
    )
