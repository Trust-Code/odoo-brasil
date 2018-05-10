# -*- coding: utf-8 -*-

from odoo import api, fields, models


class L10nBR(models.AbstractModel):
    _name = 'l10n.br'

    @api.multi
    def _compute_is_br_localization(self):
        user_id = self.env.context.get('uid')
        template_id = self.env['res.users'].browse(user_id).company_id.chart_template_id.id
        for record in self:
            if hasattr(record, 'company_id'):
                template_id = record.company_id.chart_template_id.id or template_id
            br_template = record.env['ir.model.data'].get_object('l10n_br', 'l10n_br_account_chart_template')
            br_template_id = br_template and br_template.id
            record.is_l10n_br_localization = br_template_id == template_id

    is_l10n_br_localization = fields.Boolean(
        compute=_compute_is_br_localization,
        string='Is BR localization?')

