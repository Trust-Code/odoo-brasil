# -*- coding: utf-8 -*-
{
    'name': "Importar Doc. Eletrônico Direto do Partal DFE",

    'summary': """
        Implementa funcionalidade para importar documento eletrônico diretamente
        da tela de Documentos Eletrônicos
        """,

    'description': """
        Implementa funcionalidade para importar documento eletrônico diretamente
        da tela de Documentos Eletrônicos
    """,

    'author': "Raphael Rodrigues <raphael0608@gmail.com>",

    'category': 'Uncategorized',
    'version': '11.0.0.1',

    'depends': [
        'br_dfe', 
        'br_account_einvoice_import'
        ],

    'data': [
        'views/br_dfe_import_invoice.xml',
    ],
    'installable': True,
}