# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{  # pylint: disable=C8101,C8103
    'name': 'Plano de Contas Simplificado Brasil',
    'summary': """Plano de contas simplificado""",
    'description': """Plano de contas simplificado""",
    'version': '10.0.1.0.0',
    'category': 'Localization',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'account', 'br_account'
    ],
    'data': [
        'data/br_chart_data.xml',
        'data/account.account.template.csv',
        'data/account_tax_template_data.xml',
        # TODO Achar uma forma de carregar o template
        # 'data/account_chart_template_data.yml',
    ],
    'active': False,
}
