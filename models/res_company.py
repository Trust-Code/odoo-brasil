# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015 Trustcode - www.trustcode.com.br                         #
#              Danimar Ribeiro <danimaribeiro@gmail.com>                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_cielo_id(self, cr, uid, ids, name, arg, context=None):
        Acquirer = self.pool['payment.acquirer']
        company_id = self.pool['res.users'].browse(
            cr, uid, uid,
            context=context).company_id.id
        cielo_ids = Acquirer.search(cr, uid, [
            ('website_published', '=', True),
            ('name', 'ilike', 'cielo'),
            ('company_id', '=', company_id),
        ], limit=1, context=context)
        if cielo_ids:
            cielo = Acquirer.browse(cr, uid, cielo_ids[0], context=context)
            return dict.fromkeys(ids, cielo.cielo_merchant_id)
        return dict.fromkeys(ids, False)

    def _set_cielo_id(self, cr, uid, id, name, value, arg, context=None):
        Acquirer = self.pool['payment.acquirer']
        company_id = self.pool['res.users'].browse(
            cr, uid, uid,
            context=context).company_id.id
        cielo_merchant_id = self.browse(
            cr, uid, id,
            context=context).cielo_merchant_id
        cielo_ids = Acquirer.search(cr, uid, [
            ('website_published', '=', True),
            ('cielo_merchant_id', '=', cielo_merchant_id),
            ('company_id', '=', company_id),
        ], context=context)
        if cielo_ids:
            Acquirer.write(
                cr, uid, cielo_ids, {
                    'cielo_merchant_id': value}, context=context)
        return True

    cielo_merchant_id = fields.Char(
        compute='_get_cielo_id',
        inverse='_set_cielo_id',
        nodrop=True,
        type='char', string='GUID Vendedor',
        help="ID único do vendedor para realizar vendas online."
    )
