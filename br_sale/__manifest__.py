# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Brazilian Localization Sale',
    'description': 'Brazilian Localization for Sale',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'sale', 'br_account', 'br_zip', 'br_data_account_product'
    ],
    'data': [
        'views/br_sale.xml',
        'views/sale_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_br_sale_security.xml',
    ],
    'installable': True,
    'auto_install': True
}
