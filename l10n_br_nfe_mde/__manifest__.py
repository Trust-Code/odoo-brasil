
{  # pylint: disable=C8101,C8103
    'name': 'OdooNext - Controle de Xml NFe',
    'summary': """Realiza o download e importação de xml
    Mantido por Trustcode""",
    'version': '13.0.1.0.0',
    'category': 'NFE',
    'author': 'Danimar Ribeiro',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'description': """
        Implementa a consulta de nfe periodicamente no SEFAZ
      Este módulo serve para efetuar download de notas em que são destinada
      a empresa.
      Manifesta a ciência ou desconhecimento da NF-e

      Dependencias: PyTrustNFe
    """,
    'depends': [
        'mail_bot',
        'l10n_br_nfe_import',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/mde_security.xml',
        'data/nfe_schedule.xml',
        'views/nfe_mde.xml',
        'views/res_company.xml',
        'views/eletronic_document.xml',
        'wizard/operation_not_performed.xml',
    ],
    'application': True
}
