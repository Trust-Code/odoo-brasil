# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Integração Nota Carioca',
    'description': """Efetua a integração com a prefeitura do Rio de Janeiro
        - Mantido por Trustcode""",
    'summary': """Efetua a integração com a prefeitura do Rio de Janeiro
    - Mantido por Trustcode""",
    'version': '11.0.1.0.0',
    'category': "Accounting & Finance",
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'br_nfse',
    ],
    'data': [
        'views/br_account_service.xml',
        'views/res_company.xml',
        'reports/danfpse.xml',
    ],
    'application': True,
}
