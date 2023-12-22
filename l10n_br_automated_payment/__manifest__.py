# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.


{
    'name': 'Integração Iugu',
    'version': '17.0.1.0.1',
    'category': 'Finance',
    'sequence': 5,
    'author': 'Trustcode',
    'license': 'OPL-1',
    'summary': """Realiza a integração com IUGU -
    Created by Trustcode""",
    'website': 'https://www.trustcode.com.br',
    'support': 'comercial@trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'account',
        'l10n_br_base_address',
    ],
    'external_dependencies': {
        'python': [
            'iugu',
        ],
    },
    'data': [
        'data/verify_transaction_cron.xml',
        'data/mail_template_data.xml',
        'data/bank_slip_cron.xml',
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/account_move.xml',
        'views/account_journal.xml',
        'views/portal_templates.xml',
        'views/res_config_settings.xml',
        'wizard/wizard_iugu.xml',
        'wizard/wizard_new_payment.xml',
    ],
}
