# -*- coding: utf-8 -*-
# © 2013  Renato Lima - Akretion
# © 2013  Raphaël Valyi - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Brazilian Localization Sales and Warehouse',
    'description': 'Brazilian Localization for sale_stock_module',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERPBrasil.org',
    'website': 'http://openerpbrasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'sale_stock', 'br_sale', 'br_stock_account'
    ],
    'data': [
        'views/sale_stock_view.xml',
    ],
    'auto_install': True,
}
