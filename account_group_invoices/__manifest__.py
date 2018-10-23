# -*- coding: utf-8 -*-
# © 2017 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{   # pylint: disable=C8101,C8103
    'name': "Group Invoices",
    'summary': """
    Adiciona o recurso de agrupar faturas para o mesmo cliente, respeitando
    as regras conforme configurado. Roda automáticamente conforme
    parametrização do Cron
        """,

    'description': """Group Invoices""",
    'author': "Trustcode",
    'website': "http://www.trustcode.com.br",
    'category': 'Account',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'contributors': [
        'Mackilem Van der Laan <mack.vdl@gmail.com>',
    ],
    'depends': ['br_account'],
    'data': [
        'data/ir_cron.xml'
    ],
}
