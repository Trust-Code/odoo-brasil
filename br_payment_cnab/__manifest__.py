# -*- coding: utf-8 -*-
# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{   # pylint: disable=C8101,C8103
    'name': "br_payment_cnab",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
    'author': "Trustcode",
    'website': "http://www.trustcode.com.br",
    'category': 'Uncategorized',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'contributors': [ 'Guilherme Lenon da Silva <guilhermelds@gmail.com>'
    'Marina Domingues <mgd.marinadomingues@gmail.com>'
    ],
    'depends': ['base','br_boleto'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/br_payment_cnab_views.xml',
        'views/payment_order.xml',
    ],
}
