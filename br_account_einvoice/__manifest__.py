# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account E-Invoice',
    'summary': """Base Module for the Brazilian Invoice Eletronic""",
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
        'sale',  # TODO Será que eh a melhor solução?
    ],
    'data': [
        'views/sped_tax_view.xml',
        'views/sped_eletronic_doc_view.xml',
        'views/account_invoice.xml',
    ],
    'instalable': True
}
