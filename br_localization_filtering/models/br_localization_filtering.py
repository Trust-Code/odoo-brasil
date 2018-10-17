# -*- coding: utf-8 -*-
import json
from lxml import etree

from odoo.osv import expression
from odoo import api, fields, models


class BrLocalizationFiltering(models.AbstractModel):
    _name = 'br.localization.filtering'

    def _get_br_localization_template(self):
        # We can configure in parameters if the user has a diffente tmpl id
        tmpl_id = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_br.localization.template.id', default=False)
        tmpl_id2 = self.env['ir.model.data'].xmlid_to_object(
            'br_coa.br_account_chart_template', False)
        tmpl_id3 = self.env['ir.model.data'].xmlid_to_object(
            'br_coa_simple.br_account_chart_template', False)
        return [x for x in [
            tmpl_id,
            tmpl_id2 and tmpl_id2.id or False,
            tmpl_id3 and tmpl_id3.id or False] if x]

    def _get_user_localization(self):
        user_localization = self.env.user.company_id.chart_template_id
        return user_localization and user_localization.id or False

    def _is_user_br_localization(self, user_tmpl_id):
        tmpl_ids = self._get_br_localization_template()
        return (user_tmpl_id in tmpl_ids)

    @staticmethod
    def _add_br_localization_field(doc):
        elem = etree.Element(
            'field', {
                'name': 'l10n_br_localization',
                'modifiers': '{"invisible":true, "column_invisible":true}',
            })
        nodes = doc.xpath("//tree//field") or doc.xpath("//form//field")
        if len(nodes):
            nodes[0].addnext(elem)

    def _add_br_field_to_domain(self, doc, field, view_type):
        xpaths = ["//field[@name='%s']", "//label[@for='%s']"]
        for xpath in xpaths:
            for node in doc.xpath(xpath % field):
                mod_field = (view_type == 'tree' and 'column_invisible'
                             or 'invisible')
                modifiers = json.loads(node.get("modifiers", '{}'))
                if view_type == 'tree':
                    modifiers[mod_field] = not self._is_user_br_localization()
                if view_type == 'form':
                    domain = modifiers.get(mod_field, [])
                    if isinstance(domain, bool) and domain:
                        continue
                    if domain:
                        domain = expression.normalize_domain(domain)
                    domain = expression.OR([
                        [('l10n_br_localization', '=', False)], domain])
                    modifiers[mod_field] = domain
                node.set("modifiers", json.dumps(modifiers))

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        ret_val = super(BrLocalizationFiltering, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        if view_type not in ('form', 'tree'):
            return ret_val

        doc = etree.XML(ret_val['arch'])
        self._add_br_localization_field(doc)
        for field in ret_val['fields']:
            if not field.startswith("l10n_br_"):
                continue
            if field == 'l10n_br_localization':
                continue
            self._add_br_field_to_domain(doc, field, view_type)
        ret_val['arch'] = etree.tostring(doc, encoding='unicode')
        return ret_val

    def _default_l10n_br_localization(self):
        if not hasattr(self.env.user.company_id, 'chart_template_id'):
            return True

        user_tmpl_id = self._get_user_localization()
        return self._is_user_br_localization(user_tmpl_id)

    @api.multi
    @api.depends()
    def _compute_is_br_localization(self):
        user_template = self._get_user_localization()
        for record in self:
            if hasattr(record, 'company_id'):
                user_template = (record.company_id.chart_template_id
                                 and record.company_id.chart_template_id.id
                                 or user_template)

            record.l10n_br_localization = self._is_user_br_localization(
                user_template)

    l10n_br_localization = fields.Boolean(
        compute=_compute_is_br_localization,
        default=lambda self: self._default_l10n_br_localization(),
        string='Is BR localization?')
