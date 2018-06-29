# -*- coding: utf-8 -*-
# © 2010  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Métodos de entrega no Brasil',
    'summary': """Extende os módulos do Odoo e adiciona novos métodos de
     entrega para o Brasil - Mantido por Trustcode""",
    'description': 'Métodos de entrega no Brasil',
    'license': 'AGPL-3',
    'category': 'Stock',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '11.0.1.0.0',
    'contributors': [
        'Felipe Paloschi <paloschi.eca@gmail.com>',
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_sale_stock',
        'delivery',
        'br_stock_account',
    ],
    'data': [
        'views/delivery_view.xml',
        'views/br_delivery_view.xml',
        'views/sale.xml',
        'views/stock.xml',
        'views/account_invoice.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
}
