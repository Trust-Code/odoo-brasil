# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Cielo Checkout Payment Acquirer',
    'category': 'Payment Acquirer',
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
    'application': True,
    'instalable': True,
}
