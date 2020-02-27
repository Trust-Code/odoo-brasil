# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Controle de Xml NFe',
    'summary': """Realiza o download e importação de xml
    Mantido por Trustcode""",
    'version': '12.0.1.0.0',
    'category': 'NFE',
    'author': 'Danimar Ribeiro',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
        'Fábio Luna <fabiocluna@hotmail.com>',
    ],
    'description': """
        Implementa a consulta de nfe periodicamente no SEFAZ
      Este módulo serve para efetuar download de notas em que são destinada
      a empresa.
      Manifesta a ciência ou desconhecimento da NF-e

      Dependencias: PyTrustNFe
    """,
    'depends': [
        'br_nfe',
        'br_nfe_import'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/nfe_schedule.xml',
        'views/nfe_mde.xml',
        'views/res_company.xml',
        'views/invoice_eletronic.xml',
        'wizard/operation_not_performed.xml',
    ],
    'installable': True,
    'application': True
}
