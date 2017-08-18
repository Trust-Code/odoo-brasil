# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Controle de Xml NFe',
    'summary': """Realiza o download e importação de xml
    Mantido por Trustcode""",
    'version': '10.0.1.0.0',
    'category': 'NFE',
    'author': 'Danimar Ribeiro',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'description': """
        Implementa a consulta de nfe periodicamente no SEFAZ
      Este módulo serve para efetuar download de notas em que são destinada
      a empresa.
      Manifesta a ciência ou desconhecimento da NF-e

      Dependencias: PyTrustNFe
    """,
    'depends': [
        'br_nfe',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/nfe_schedule.xml',
        'views/nfe_mde.xml',
        'views/res_company.xml'
    ],
    'installable': True,
    'application': True
}
