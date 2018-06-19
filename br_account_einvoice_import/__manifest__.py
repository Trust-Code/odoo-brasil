# -*- coding: utf-8 -*-
# © 2018 Raphael Rodrigues, raphael0608@gmail.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Brazilian Localization Import Eletronic Invoice",

    'summary': """
        Criação de Faturas através da importação de Documentos Eletrônicos por meio
        de arquivo XML
        """,

    'description': """
        Criação de Faturas através da importação de Documentos Eletrônicos por meio
        de arquivo XML
    """,

    'author': 'Raphael Rodrigues <raphael0608@gmail.com>',

    'category': 'others',
    'version': '11.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['br_base',
                'br_nfe',
                'br_purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'wizard/einvoice_import.xml',
    ],
    'installable': True,
}