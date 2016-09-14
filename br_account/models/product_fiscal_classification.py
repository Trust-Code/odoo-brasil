# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductFiscalClassification(models.Model):
    _name = 'product.fiscal.classification'
    _description = u'Classificações Fiscais (NCM)'

    code = fields.Char(string=u"Código", size=14)
    name = fields.Char(string="Nome", size=200)
    company_id = fields.Many2one('res.company', string="Empresa")
    type = fields.Selection([('view', u'Visão'),
                             ('normal', 'Normal'),
                             ('extension', u'Extensão')], 'Tipo')
    parent_id = fields.Many2one('product.fiscal.classification', string="Pai")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result
