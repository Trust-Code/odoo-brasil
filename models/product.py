# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type_product = fields.Selection([
        ('00', u'00 - Mercadoria para Revenda'),
        ('01', u'01 - Matéria-Prima'),
        ('02', u'02 - Embalagem'),
        ('03', u'03 - Produto em Processo'),
        ('04', u'04 - Produto Acabado'),
        ('05', u'05 - Subproduto'),
        ('06', u'06 - Produto Intermediário'),
        ('07', u'07 - Material de Uso e Consumo'),
        ('08', u'08 - Ativo Imobilizado'),
        ('09', u'09 - Serviços'),
        ('10', u'10 - Outros insumos'),
        ('99', u'99 - Outras')        
     ], 'Tipo do Item',
    default='00')
    sped_ids = fields.One2many('product.template.sped', 'product_id', 'Alteração Cadastro', copy=False)

    @api.multi
    def write(self, vals):
        values = {}
        values['product_id'] = self.id
        if 'name' in vals:
            values['name'] = 'Descrição'
            values['ocorrido'] = 'Alterado'
            values['valor_anterior'] = self.name
            values['valor_novo'] = vals.get('name')
            self.sped_ids.create(values)                    
        if 'default_code' in vals:
            values['name'] = 'Código'
            values['ocorrido'] = 'Alterado'
            values['valor_anterior'] = self.default_code
            values['valor_novo'] = vals.get('default_code')
            self.sped_ids.create(values)                    
            
        return super(ProductTemplate, self).write(vals)        


class ProductUom(models.Model):
    _inherit = 'product.uom'
    
    
    description = fields.Char('Descrição')
    type_uom = fields.Selection([
        ('int', u'Unidade uso interno'),
        ('ext', u'Unidade Terceiros')], default='ext')


class ProductTemplateSped(models.Model):
    _name = "product.template.sped"

    product_id = fields.Many2one('product.template', 'Produto')
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        index=True,
        default=lambda self: self.env.user,
        readonly=True
        )
    name = fields.Char(u'Campo', readonly=True)
    ocorrido = fields.Char(u'Ocorrencia', readonly=True)
    date_change = fields.Datetime(
       u'Data Alteração',
       default=fields.Datetime.now,
       readonly=True
      )
    valor_anterior = fields.Char(u'Anterior', readonly=True)
    valor_novo = fields.Char(u'Novo', readonly=True)


    _order = "date_change desc"
