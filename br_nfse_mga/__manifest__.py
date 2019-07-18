# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Integração Nota Maringá',
    'description': """Efetua a integração com a prefeitura de Maringá
        - Mantido por Trustcode""",
    'summary': """Efetua a integração com a prefeitura de Maringá
    - Mantido por Trustcode""",
    'version': '12.0.1.0.0',
    'category': "Accounting & Finance",
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
        'Johny Chen Jy <johnychenjy@gmail.com>',
    ],
    'depends': [
        'br_nfse',
    ],
    'data': [
        'views/br_account_service.xml',
        'views/res_company.xml',
        'views/account_invoice.xml',
        'reports/danfpse.xml',
    ],
    'application': True,
}
