# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Odoo Brasil - WMS Accounting',
    'summary': """Realiza o link entre faturas e o estoque e logistica""",
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'stock_account', 'br_account',
    ],
    'data': [
        'views/account_invoice.xml',
    ],
    'instalable': True,
}
