# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2010  Renato Lima - Akretion                                  #
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

{
    'name': 'Métodos de entrega no Brasil',
    'summary': """Extende os módulos do Odoo e adiciona novos métodos de
     entrega para o Brasil - Mantido por Trustcode""",
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'br_sale_stock',
        'delivery',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/delivery_view.xml',
        'views/stock_view.xml',
        'views/l10n_br_delivery_view.xml',
        'security/ir.model.access.csv',
    ],
    'category': 'Localisation',
    'application': True,
}
