# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

{
    'name': 'Importar xml para invoice',
    'description' : 'Others',
    'version': '1.0',
    'category': 'Other',
    'author': 'ATS Solucoes',
    'website': 'http://www.atsti.com.br',
    'license': 'AGPL-3',
    'contributors': [
        'Otávio Munhoz<otaviosilmunhoz@hotmail.com>',
    ],
    'depends': [
        'account',
        'br_nfe',
        #'br_cte',
        'br_account_einvoice',
        'nfe_purchase_import',
        'br_stock_account',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'wizard/import_xml_wizard_view.xml',
    ],
    'demo': [],
    'installable': True,
}
