# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Odoo Brasil - Account Product',
    'summary': """Brazilian Localization Account""",
    'version': '9.0.1.0.0',
    'category': 'Localisation',
    'author': 'Akretion',
    'license': 'AGPL-3',
    'website': 'http://odoo-brasil.org',
    'depends': [
        'l10n_br_data_account',
    ],
    'data': [
        'views/br_account_product_view.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'views/res_company_view.xml',
    ],
}
