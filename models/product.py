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
        ('00', u'Mercadoria Revenda'),
        ('01', u'Matéria Prima'),
        ('02', u'Embalagem'),
        ('03', u'Produto em Processo'),
        ('04', u'Produto Acabado'),
        ('05', u'Subproduto'),
        ('06', u'Produto Intermediário'),
        ('07', u'Material de Uso e Consumo'),
        ('08', u'Ativo Imobilizado'),
        ('09', u'Serviços'),
        ('10', u'Outros Insumos'),
        ('99', u'Outros')
     ], 'Tipo do Item',
    default='00')


class ProductUom(models.Model):
    _inherit = 'product.uom'
    
    
    description = fields.Char('Descrição')
