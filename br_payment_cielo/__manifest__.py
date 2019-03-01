# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Cielo Checkout Payment Acquirer',
    'category': 'Payment Acquirer',
    'summary': 'Payment Acquirer: Cielo Checkout Implementation',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Trustcode',
    'depends': [
        'account',
        'payment',
        'website_sale',
        'br_base',
    ],
    'data': [
        'views/cielo.xml',
        'views/payment_acquirer.xml',
        'views/res_config_view.xml',
        'data/cielo.xml',
    ],
    'application': True,
    'installable': True,
}
