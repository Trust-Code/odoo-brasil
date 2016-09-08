# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Sale',
    'description': 'Brazilian Localization for Sale',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '9.0.1.0.0',
    'depends': [
        'sale', 'l10n_br_account_new',
    ],
    'data': [
        'views/sale_view.xml',
        'views/res_config_view.xml',
        'views/res_company_view.xml',
        # 'security/ir.model.access.csv',
        'security/l10n_br_sale_security.xml',
        'data/l10n_br_sale_data.xml',
        'report/sale_report_view.xml',
    ],
    'demo': ['demo/l10n_br_sale_demo.xml'],
    'installable': True,
    'auto_install': True
}
