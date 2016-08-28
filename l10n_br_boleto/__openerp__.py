# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Payment (Boleto)',
    'summary': """Module to print brazilian boleto's""",
    'version': '9.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'l10n_br_account_new',
    ],
    'data': [
        'views/account_invoice.xml',
        'views/account_move_line.xml',
        'views/res_company.xml',
        'views/payment_mode.xml',
        'reports/report_print_button_view.xml',
    ],
    'instalable': True
}
