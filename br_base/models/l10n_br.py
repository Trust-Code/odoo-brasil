# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from lxml import etree

from odoo.osv import expression
from odoo import api, fields, models


class L10nBR(models.AbstractModel):
    _name = 'l10n.br'

    def _get_user_localization(self):
        user_id = self.env.context.get('uid')
        template_id = self.env['res.users'].browse(
            user_id).company_id.chart_template_id.id
        br_template = self.env['ir.model.data'].get_object(
            'br_coa_simple', 'br_account_chart_template')
        br_template_id = br_template and br_template.id
        return br_template_id == template_id

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        ret_val = super(L10nBR, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        if view_type not in ('form', 'tree'):
            return ret_val

        doc = etree.XML(ret_val['arch'])
        for field in ret_val['fields']:
            if not field.startswith("l10n_br_"):
                continue
            if field == 'l10n_br_localization':
                continue

            for node in doc.xpath("//field[@name='%s']" % field):
                mod_field = (view_type == 'tree' and 'column_invisible'
                             or 'invisible')
                modifiers = json.loads(node.get("modifiers"))
                if view_type == 'tree':
                    modifiers[mod_field] = not self._get_user_localization()
                if view_type == 'form':
                    domain = modifiers.get(mod_field, [])
                    domain = expression.OR([domain, [
                        ('l10n_br_localization', '=', False)]])
                    modifiers[mod_field] = domain
                node.set("modifiers", json.dumps(modifiers))

        ret_val['arch'] = etree.tostring(doc, encoding='unicode')
        return ret_val

    @api.multi
    @api.depends('company_id')
    def _compute_is_br_localization(self):
        user_template_id = self._get_user_localization()
        for record in self:
            if hasattr(record, 'company_id'):
                user_template_id = (record.company_id.chart_template_id.id
                                    or user_template_id)
            br_template = record.env['ir.model.data'].get_object(
                'br_coa_simple', 'br_account_chart_template')
            br_template_id = br_template and br_template.id
            record.l10n_br_localization = br_template_id == user_template_id

    l10n_br_localization = fields.Boolean(
        compute=_compute_is_br_localization,
        string='Is BR localization?')
