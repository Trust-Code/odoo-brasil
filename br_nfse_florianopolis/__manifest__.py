# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Exportação XML NFS-e - Florianópolis',
    'description': "Realiza a exportação em xml das notas fiscais de serviço",
    'summary': "Realiza a exportação em xml das notas fiscais de serviço",
    'version': '11.0.1.0.0',
    'category': "Accounting & Finance",
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'br_account',
    ],
    'data': [
        'wizard/nfse_florianopolis_export_view.xml',
    ],
}
