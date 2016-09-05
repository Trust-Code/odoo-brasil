# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from odoo import api, fields, models


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    def _get_default_copy_note(self):
        ir_values = self.env['ir.values']
        comp_id = self.env.user.company_id.id
        return ir_values.get_default('sale.order', 'copy_note',
                                     company_id=comp_id)

    copy_note = fields.Boolean(u'Copiar Observações nos Documentos Fiscais',
                               default=_get_default_copy_note)

    @api.multi
    def set_sale_defaults(self):
        result = super(SaleConfiguration, self).set_sale_defaults()
        ir_values = self.env['ir.values']
        user = self.env.user
        ir_values.set_default('sale.order', 'copy_note',
                              self.copy_note, company_id=user.company_id.id)
        return result
