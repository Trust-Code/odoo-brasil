# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.exceptions import RedirectWarning


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def create(self, values):
        res = super(PosSession, self).create(values)
        config_id = values.get('config_id') or self.env.context.get(
            'default_config_id')
        pos_config = self.env['pos.config'].browse(config_id)

        fpo_id = self.env.ref('account.action_account_fiscal_position_form').id
        msg = 'Configurar posições fiscais'
        if not pos_config.default_fiscal_position_id:
            raise RedirectWarning(
                'Configure uma posição fiscal padrão para o POS',
                self.env.ref('point_of_sale.action_pos_config_pos').id,
                msg)
        if not pos_config.default_fiscal_position_id.product_document_id:
            raise RedirectWarning(
                'Configure um tipo de documento na posição fiscal',
                fpo_id, msg)
        if not pos_config.default_fiscal_position_id.product_serie_id:
            raise RedirectWarning(
                'Configure uma série de produto na posição fiscal',
                fpo_id, msg)
        if not pos_config.default_fiscal_position_id.icms_tax_rule_ids:
            raise RedirectWarning(
                'Configure pelo menos uma regra de ICMS na posição fiscal',
                fpo_id, msg)
        if not pos_config.default_fiscal_position_id.ipi_tax_rule_ids:
            raise RedirectWarning(
                'Configure pelo menos uma regra de IPI na posição fiscal',
                fpo_id, msg)
        if not pos_config.default_fiscal_position_id.pis_tax_rule_ids:
            raise RedirectWarning(
                'Configure pelo menos uma regra de PIS na posição fiscal',
                fpo_id, msg)
        if not pos_config.default_fiscal_position_id.cofins_tax_rule_ids:
            raise RedirectWarning(
                'Configure pelo menos uma regra de COFINS na posição fiscal',
                fpo_id, msg)
        for journal in pos_config.journal_ids:
            if not journal.metodo_pagamento:
                raise RedirectWarning(
                    'Configure o método de pagamento no diário %s' %
                    journal.name,
                    self.env.ref('account.action_account_journal_form').id,
                    'Configure os método de pagamento')
        return res
