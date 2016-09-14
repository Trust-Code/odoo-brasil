# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Pagamentos via Boleto Bancário',
    'summary': """Permite gerar e realizar a integração bancária através de
        arquivo CNAB 240 - Mantido por Trustcode""",
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_account',
    ],
    'data': [
        'views/account_invoice.xml',
        'views/account_move_line.xml',
        'views/res_company.xml',
        'views/payment_mode.xml',
        'reports/report_print_button_view.xml',
    ],
    'instalable': True,
    'application': True,
}
