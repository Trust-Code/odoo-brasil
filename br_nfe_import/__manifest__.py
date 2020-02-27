# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{  # pylint: disable=C8101,C8103
    'name': 'Importação de Documento Fiscal Eletronico',
    'version': '12.0.1.0.0',
    'category': 'Account addons',
    'license': 'AGPL-3',
    'author': 'Trustcode',
    'website': 'http://www.trustcode.com.br',
    'description': """
        Implementa funcionalidade para importar xml da nfe.""",
    'contributors': [
        'Fábio Luna <fabiocluna@hotmail.com>',
        'Alessandro Fernandes Martini <alessandrofmartini@gmail.com>',
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'sale',
        'br_nfe',
        'br_purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/account_invoice.xml',
        'views/invoice_eletronic.xml',
        'views/product_category.xml',
        'wizard/import_nfe.xml',
    ],
    'installable': True,
}
