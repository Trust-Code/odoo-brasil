{  # pylint: disable=C8101,C8103
    'name': 'Importação de CTE',
    'version': '12.0.1.0.0',
    'category': 'Account addons',
    'license': 'AGPL-3',
    'author': 'Code137',
    'website': 'http://www.code137.com.br',
    'description': """
        Implementa funcionalidade para importar xml da CTE
        como fatura de fornecedor.""",
    'contributors': [
        'Felipe Paloschi <paloschi.eca@gmail.com>',
    ],
    'depends': [
        'delivery',
        'br_nfe_mde',
        'br_nfe_import',
    ],
    'data': [
        "data/data.xml",
        "wizard/import_cte.xml",
    ],
    'installable': True,
}
