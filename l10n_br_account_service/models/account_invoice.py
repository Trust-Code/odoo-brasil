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

from lxml import etree
from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False,
                        toolbar=False, submenu=False):

        result = super(AccountInvoiceLine, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        context = self._context
        if view_type == 'form':
            eview = etree.fromstring(result['arch'])

            if 'type' in context.keys():
                cfops = eview.xpath("//field[@name='cfop_id']")
                for cfop_id in cfops:
                    cfop_id.set('domain', "[('type','=','%s')]" % (
                        OPERATION_TYPE[context['type']],))
                    cfop_id.set('required', '1')

            if context.get('fiscal_type', False) == 'service':

                cfops = eview.xpath("//field[@name='cfop_id']")
                for cfop_id in cfops:
                    cfop_id.set('invisible', '1')
                    cfop_id.set('required', '0')

            result['arch'] = etree.tostring(eview)

        return result
