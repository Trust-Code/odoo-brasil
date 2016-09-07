# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
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


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _get_taxes(self):
        for company in self:        
            product_tax_ids = [tax.tax_id.id for tax in
                               company.product_tax_definition_line]
            service_tax_ids = [tax.tax_id.id for tax in
                               company.service_tax_definition_line]
            product_tax_ids.sort()
            service_tax_ids.sort()
            company.product_tax_ids = product_tax_ids
            company.service_tax_ids = service_tax_ids

    product_tax_ids = fields.Many2many('account.tax', compute=_get_taxes,
                                       string='Product Taxes')
    service_tax_ids = fields.Many2many('account.tax', compute=_get_taxes,
                                       string='Service Taxes')
    