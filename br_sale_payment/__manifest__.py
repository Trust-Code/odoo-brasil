# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Brazilian Localization Sale Payment',
    'description': 'Brazilian Localization for Sale Payment',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Trustcode',
    'website': 'http://www.trustcode.com.br',
    'version': '12.0.1.0.0',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'sale', 'br_account_payment',
    ],
    'data': [
        'views/sale_order.xml',
    ],
    'auto_install': True
}
