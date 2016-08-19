# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Account',
    'summary': """Brazilian Localization Account""",
    'version': '9.0.1.0.0',
    'category': 'pos',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'account', 'l10n_br_base'
    ],
    'data': [
        'views/account_fiscal_position_view.xml',
        'views/account_invoice_view.xml',
        'views/l10n_br_account_view.xml',
        'views/product_view.xml',
        'views/res_company_view.xml',
        'views/account_tax.xml',
        'security/ir.model.access.csv',
    ],
}
