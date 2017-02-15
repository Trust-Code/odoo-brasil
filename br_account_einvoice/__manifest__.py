# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account E-Invoice',
    'summary': """Base Module for the Brazilian Invoice Eletronic""",
    'description': """Base Module for the Brazilian Invoice Eletronic""",
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'document',
        'br_base',
        'br_account',
        'br_data_account',
    ],
    'data': [
        'data/nfe_cron.xml',
        'data/br_account_einvoice.xml',
        'security/ir.model.access.csv',
        'views/invoice_eletronic.xml',
        'views/account_invoice.xml',
        'views/account_config_settings.xml',
    ],
    'installable': True
}
