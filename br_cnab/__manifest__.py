# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Generate CNAB Files',
    'summary': """Base Module for the Brazilian Cnab Files""",
    'description': """Base Module for the Brazilian Cnab Files""",
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_boleto'
    ],
    'external_dependencies': {
        'python': [
            'cnab240', 'cnab240.tipos'
        ],
    },
    'data': [
        'sequence/br_cnab_sequence.xml',
        'views/payment_order.xml',
    ],
    'installable': True
}
