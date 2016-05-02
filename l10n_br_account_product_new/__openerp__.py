# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Account',
    'summary': """Brazilian Localization Account""",
    'version': '9.0.1.0.0',
    'category': 'Localisation',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://odoo-brasil.org',
    'depends': [
        'l10n_br_data_account',
    ],
    'data': [
        'data/l10n_br_account_product.cfop.csv',
        'data/l10n_br_account.fiscal.document.csv',
        'views/l10n_br_account_product_view.xml',
    ],
}
