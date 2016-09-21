# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Generate CNAB Files',
    'summary': """Base Module for the Brazilian Cnab Files""",
    'description': """Base Module for the Brazilian Cnab Files""",
    'version': '9.0.1.0.0',
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
    'data': [
        'views/payment_order.xml',
        'views/payment_mode.xml',
        'views/payment_type.xml'
    ],
    'instalable': True
}
