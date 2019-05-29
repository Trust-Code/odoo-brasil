# © 2019 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models, _


class ProductUom(models.Model):
    _inherit = 'uom.uom'

    l10n_br_description = fields.Char(string="Description", size=60)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_br_sped_type = fields.Selection(
        [(0, '00 - Mercadoria para Revenda'),
         (1, '01 - Matéria Prima'),
         (2, '02 - Embalagem'),
         (3, '03 - Produto em Processo'),
         (4, '04 - Produto Acabado'),
         (5, '05 - Subproduto'),
         (6, '06 - Produto Intermediário'),
         (7, '07 - Material de uso e consumo'),
         (8, '08 - Ativo Imobilizado'),
         (9, '09 - Serviços'),
         (10, '10 - Outros insumos'),
         (99, '99 - Outras')], string="SPED Type", default=0)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    _sql_constraints = [
        ('default_code_uniq', 'unique (default_code)',
         _('Product Reference must be unique!'))
    ]

    @api.multi
    def write(self, vals):
        for product in self:
            values = {}
            values['product_id'] = product.id
            if 'name' in vals:
                values['name'] = 'name'
                values['old_value'] = product.name
                values['new_value'] = vals.get('name')
                self.env['l10n_br.product.changes'].sudo().create(values)
            if 'default_code' in vals:
                values['name'] = 'default_code'
                values['old_value'] = product.default_code
                values['new_value'] = vals.get('default_code')
                self.env['l10n_br.product.changes'].sudo().create(values)

        return super(ProductProduct, self).write(vals)


class L10nBrProductChanges(models.Model):
    _name = "l10n_br.product.changes"

    product_id = fields.Many2one('product.product', 'Product')
    name = fields.Char('Field name', readonly=True, size=30)
    changed_date = fields.Datetime(
        string='Changed Date', default=fields.Datetime.now, readonly=True)
    old_value = fields.Char('Old value', readonly=True)
    new_value = fields.Char('New value', readonly=True)
