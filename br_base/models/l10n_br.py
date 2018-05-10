import json
from lxml import etree

from odoo.osv import expression
from odoo import api, fields, models


class L10nBR(models.AbstractModel):
    _name = 'l10n.br'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        ret_val = super(L10nBR, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        if view_type != 'form':
            return ret_val

        doc = etree.XML(ret_val['arch'])
        for field in ret_val['fields']:
            if not field.startswith("l10n_br_"):
                continue
            if field == 'l10n_br_localization':
                continue

            for node in doc.xpath("//field[@name='%s']" % field):
                modifiers = json.loads(node.get("modifiers"))
                domain = modifiers.get('invisible', [])
                domain = expression.OR([domain, [
                    ('l10n_br_localization', '=', False)]])
                modifiers['invisible'] = domain
                node.set("modifiers", json.dumps(modifiers))

        ret_val['arch'] = etree.tostring(doc, encoding='unicode')
        return ret_val

    @api.multi
    @api.depends('company_id')
    def _compute_is_br_localization(self):
        user_id = self.env.context.get('uid')
        template_id = self.env['res.users'].browse(
            user_id).company_id.chart_template_id.id
        for record in self:
            if hasattr(record, 'company_id'):
                template_id = \
                    record.company_id.chart_template_id.id or template_id
            br_template = record.env['ir.model.data'].get_object(
                'br_coa_simple', 'br_account_chart_template')
            br_template_id = br_template and br_template.id
            record.l10n_br_localization = br_template_id == template_id

    l10n_br_localization = fields.Boolean(
        compute=_compute_is_br_localization,
        string='Is BR localization?')
