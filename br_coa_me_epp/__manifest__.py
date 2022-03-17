# © 2019 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{  # pylint: disable=C8101,C8103
    'name': 'Plano de Contas para Microempresa e Empresa de Pequeno Porte',
    'summary': "Plano de Contas para Microempresa e Empresa de Pequeno Porte",
    'description': """Plano de Contas para Microempresa e EPP""",
    'version': '13.0.1.0.0',
    'category': 'Accounting/Localizations/Account Charts',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
        'Jonatas Biazus <jonatasbiazusct@gmail.com>',
    ],
    'depends': [
        'account',
    ],
    'data': [
        'data/br_chart_data.xml',
        'data/account_group_template.xml',
        'data/account.account.template.csv',
        'data/account_tax_template_data.xml',

    ],
    'active': True,
}
