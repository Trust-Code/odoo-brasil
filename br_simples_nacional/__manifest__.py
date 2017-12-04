# -*- coding: utf-8 -*-
# © 2017 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{
    'name': "Simples Nacional",

    'summary': """
        Calcular a alíquota efetiva do Simples Nacional""",

    'description': """
    """,
    'author': "Trustcode",
    'website': "http://www.trustcode.com.br",
    'category': 'Uncategorized',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'contributors': [
        'Felipe Paloschi <paloschi.eca@gmail.com>',
    ],
    'depends': ['br_account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/simples_nacional_view.xml',
    ],
}
