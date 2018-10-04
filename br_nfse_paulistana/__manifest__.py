# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Envio de NFS-e - Paulistana',
    'summary': """Permite o envio de NFS-e Paulistana através das faturas do Odoo
    Mantido por Trustcode""",
    'description': 'Envio de NFS-e - Nota Fiscal Paulistana',
    'version': '11.0.1.0.0',
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
    'external_dependencies': {
        'python': [
            'pytrustnfe.nfse.paulistana', 'pytrustnfe.certificado'
        ],
    },
    'data': [
        'views/br_account_service.xml',
        'views/invoice_eletronic.xml',
        'reports/danfse_sao_paulo.xml',
    ],
    'installable': True,
    'application': True,
}
