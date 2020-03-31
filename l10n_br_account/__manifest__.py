{  # pylint: disable=C8101,C8103
    'name': 'Odoo Next - Enable tax calculations',
    'description': 'Enable Tax Calculations',
    'version': '13.0.1.0.0',
    'category': 'Localization',
    'author': 'Trustcode',
    'license': 'OEEL-1',
    'website': 'http://www.odoo-next.com,br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fiscal_position.xml',
        'views/account_tax.xml',
    ],
}
