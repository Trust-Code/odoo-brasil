{  # pylint: disable=C8101,C8103
    'name': 'Odoo Next - ',
    'description': 'Enable Tax Calculations',
    'version': '14.0.1.0.0',
    'category': 'Localization',
    'author': 'Code 137',
    'license': 'OEEL-1',
    'website': 'http://www.code137.com.br',
    'contributors': [
        'Fábio Luna <fabiocluna@hotmail.com>',
    ],
    'depends': [
        'stock_account',
    ],
    'data': [
        'views/stock_picking.xml',
    ],
}
