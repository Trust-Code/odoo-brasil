# © 2019 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{   # pylint: disable=C8101,C8103
    'name': "Define Taxes as Python Code - Pass extra variables",
    'summary': "Allows to use python code to define taxes",
    'description': """Allows to use python code to define taxes -
        Define extra variables to calculate taxes in Brazil""",
    'author': "Trustcode",
    'website': "http://www.trustcode.com.br",
    'category': 'account',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'contributors': [
        'Mackilem Van der Laan <mack.vdl@gmail.com>',
    ],
    'depends': [
        'br_account',
        'account_tax_python'
    ],
    'data': [
        'data/account_tax_data.xml'
    ],
}
