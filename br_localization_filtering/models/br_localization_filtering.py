# -*- coding: utf-8 -*-
import json
from lxml import etree

from odoo.osv import expression
from odoo import api, fields, models


class BrLocalizationFiltering(models.AbstractModel):
    _name = 'br.localization.filtering'

    # TODO add br_coa_simple
    def _get_br_localization_template(self):
        return self.env['ir.model.data'].xmlid_to_object(
            'br_coa.br_account_chart_template', False)

    def _get_user_localization(self):
        return self.env.user.company_id.chart_template_id

    def _is_user_localization(self):
        return (self._get_br_localization_template() ==
                self._get_user_localization())

    # TODO add invisible attribute to l10n_br_localization field
    @staticmethod
    def _add_localization_field(doc):
        elem = etree.Element(
            'field', {
                'name': 'l10n_br_localization',
                # 'invisible': '1',
            })
        nodes = doc.xpath("//tree//field") or doc.xpath("//form//field")
        if len(nodes):
            nodes[0].addnext(elem)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        ret_val = super(BrLocalizationFiltering, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        if view_type not in ('form', 'tree'):
            return ret_val

        doc = etree.XML(ret_val['arch'])
        self._add_localization_field(doc)
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
                    modifiers[mod_field] = not self._is_user_localization()
                if view_type == 'form':
                    domain = modifiers.get(mod_field, [])
                    domain = expression.OR([domain, [
                        ('l10n_br_localization', '=', False)]])
                    modifiers[mod_field] = domain
                node.set("modifiers", json.dumps(modifiers))

        ret_val['arch'] = etree.tostring(doc, encoding='unicode')
        return ret_val

    def _default_l10n_br_localization(self):
        if not hasattr(self.env.user.company_id, 'chart_template_id'):
            return True

        return self._is_user_localization()

    @api.multi
    @api.depends()
    def _compute_is_br_localization(self):
        user_template = self._get_user_localization()
        for record in self:
            if hasattr(record, 'company_id'):
                user_template = (record.company_id.chart_template_id
                                 or user_template)
            br_template = self._get_br_localization_template()
            record.l10n_br_localization = br_template.id == user_template.id

    l10n_br_localization = fields.Boolean(
        compute=_compute_is_br_localization,
        default=lambda self: self._default_l10n_br_localization(),
        string='Is BR localization?')
