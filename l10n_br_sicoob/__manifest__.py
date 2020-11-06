# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.


{
    'name': 'Integração Sicoob - Extrato Bancário',
    'version': '11.0.1.0.0',
    'category': 'Finance',
    'sequence': 5,
    'author': 'Trustcode',
    'license': 'OPL-1',
    'summary': """Realiza a integração com Sicoob Extrato Bancário -
    Created by Trustcode""",
    'website': 'https://www.trustcode.com.br',
    'support': 'comercial@trustcode.com.br',
    'price': '180',
    'currency': 'EUR',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'account',
    ],
    'data': [
        'views/res_bank_views.xml',
        'views/account_journal_views.xml',
        'wizard/setup_wizard_views.xml',
    ],
    'application': True,
}
