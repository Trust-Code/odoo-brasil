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


{
    'name': 'Cielo Checkout Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Cielo Checkout Implementation',
    'version': '1.0',
    'description': """Cielo Checkout Payment Acquirer""",
    'author': 'Trustcode',
    'depends': ['payment', 'website_sale', 'br_base'],
    'data': [
        'views/cielo.xml',
        'views/payment_acquirer.xml',
        'views/res_config_view.xml',
        'data/cielo.xml',
    ],
    'installable': False,
}
