# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Brazilian Localization Purchase and Warehouse',
    'description': 'Brazilian Localization Purchase and Warehouse Link',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Trustcode',
    'website': 'http://www.trustcode.com.br',
    'version': '10.0.1.0.0',
    'depends': [
        'br_purchase', 'br_stock_account'
    ],
    'data': [
        'views/purchase_stock_view.xml',
    ],
    'auto_install': True,
}
