# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Importação de extratos bancários',
    'summary': """Importação de extratos bancários nos formatos OFX e
    Cnab 240 - Mantido por Trustcode""",
    'description': 'Import Cnab Files',
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'account_bank_statement_import'
    ],
    'external_dependencies': {
        'python': [
            'cnab240', 'cnab240.bancos', 'cnab240.tipos', 'ofxparse'
        ],
    },
    'data': [
        'views/account_bank_statement_import.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
}
