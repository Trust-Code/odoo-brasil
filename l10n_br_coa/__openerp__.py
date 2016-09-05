# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{
    'name': 'Plano de Contas Simplificado Brasil',
    'summary': """Plano de contas simplificado""",
    'version': '8.0',
    'category': 'Localization/Account Charts',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'account',
    ],
    'data': [
        'data/account.account.template.csv',
        'data/l10n_br_chart_data.xml',
        'data/account_tax_template_data.xml',
    ],
    'instalable': True,
    'auto_install': False,
}
