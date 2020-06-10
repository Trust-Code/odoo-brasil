# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Envio de NFS-e Imperial',
    'summary': """Permite o envio de NFS-e Imperial através das faturas do Odoo
    Mantido por Trustcode""",
    'description': 'Envio de NFS-e - Imperial',
    'version': '12.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_nfse',
    ],
    'data': [
        'views/res_company.xml',
        'reports/danfse_imperial.xml',
    ],
    'installable': True,
    'application': True,
}
