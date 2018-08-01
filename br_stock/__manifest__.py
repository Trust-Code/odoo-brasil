# -*- coding: utf-8 -*-
# © 2018 Raphael Rodrigues, Keetech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Odoo Brasil - BR Stock',
    'summary': """Algumas extensões do módulo 'Stock' para a versão brasileira""",
    'description': 'Estensões e customizações do stock para o Brasil',
    'version': '11.0.1.0.0',
    'category': 'Inventory',
    'author': 'Keetech',
    'license': 'AGPL-3',
    'website': 'http://www.keetech.com.br',
    'contributors': [
        'Raphael Rodrigues <raphael0608@gmail.com>',
    ],
    'depends': [
        'stock'
    ],
    'data': [
        'views/br_stock.xml',
    ],
    'auto_install': True,
}