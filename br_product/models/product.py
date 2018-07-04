# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('barcode')
    def _onchange_barcode(self):
        cod_barras = self.barcode
        if self.barcode:
            if len(cod_barras) == 12:
                position_impar = [cod_barras[0], cod_barras[2], cod_barras[4], cod_barras[6], cod_barras[8], cod_barras[10]]
                position_par = [cod_barras[1], cod_barras[3], cod_barras[5], cod_barras[7], cod_barras[9]]
                dig_validador = int(cod_barras[11])
                total_impar = [int(x) for x in position_impar]
                total_par = [int(x) for x in position_par]
                total = sum(total_impar) * 3 + sum(total_par)
                if ((total + dig_validador) % 10) == 0:
                    self.barcode = cod_barras
                else:
                    raise UserError(_(u'Código de Barras inválido, insira um código de barras válido!'))
            elif len(cod_barras) == 13:
                position_impar = [cod_barras[0], cod_barras[2], cod_barras[4], cod_barras[6], cod_barras[8],
                                  cod_barras[10]]
                position_par = [cod_barras[1], cod_barras[3], cod_barras[5], cod_barras[7], cod_barras[9], cod_barras[11]]
                dig_validador = int(cod_barras[12])
                total_impar = [int(x) for x in position_impar]
                total_par = [int(x) for x in position_par]
                total = sum(total_impar) + sum(total_par) * 3
                if ((total + dig_validador) % 10) == 0:
                    self.barcode = cod_barras
                else:
                    raise UserError(_(u'Código de Barras inválido, insira um código de barras válido!'))
            else:
                raise UserError(_(u'Código de Barras inválido, insira um código de barras válido!'))

    @api.one
    @api.constrains('default_code')
    def _check_default_code_duplicated(self):
        """ Check if the field default_code has duplicated value
        """
        if not self.default_code:
            return True
        product_ids = self.search(
            ['&', ('default_code', '=', self.default_code), ('id', '!=', self.id)])

        if len(product_ids) > 0:
            raise UserError(_(u'Já existe um produto cadastrado com o código informado!'))
        return True

    @api.one
    @api.constrains('name')
    def _check_name_duplicated(self):
        """ Check if the field name has duplicated value
        """
        product_ids = self.search(
            ['&', ('name', '=', self.name), ('id', '!=', self.id)])

        if len(product_ids) > 0:
            raise UserError(_(u'Já existe um produto cadastrado com o nome informado!'))
        return True