# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Contas a Pagar e Receber',
    'summary': """Facilita a visualização de parcelas a pagar e receber
    no Odoo - Mantido por Trustcode""",
    'description': """Facilita a visualização de parcelas a pagar e receber
    no Odoo - Mantido por Trustcode""",
    'version': '10.0.1.0.0',
    'category': 'Invoicing & Payments',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
        'Carlos Alberto Cipriano Korovsky <carlos.korovsky@uktech.com.br',
    ],
    'depends': [
        'br_account',
        'account_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice.xml',
        'views/br_account_payment.xml',
        'views/payment_mode.xml',
        'views/account_payment.xml',
        'views/account_journal.xml',
    ],
    'installable': True,
    'application': True,
}
