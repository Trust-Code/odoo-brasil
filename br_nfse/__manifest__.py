# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Módulo base para envio de NFS-e',
    'summary': """Permite o envio de NFS-e através das faturas do Odoo
    Mantido por Trustcode""",
    'description': 'Módulo base para envio de NFS-e',
    'version': '12.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_account_einvoice',
    ],
    'external_dependencies': {
        'python': [
            'pytrustnfe.certificado'
        ],
    },
    'data': [
        'views/account_invoice.xml',
        'views/invoice_eletronic.xml',
        'wizard/cancel_nfse.xml',
    ],
    'installable': True,
}
