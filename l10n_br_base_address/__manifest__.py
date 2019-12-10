{  # pylint: disable=C8101,C8103
    'name': 'Odoo Next - Address Extension',
    'description': 'Modifies address forms',
    'version': '13.0.1.0.0',
    'category': 'Localization',
    'license': 'OEEL-1',
    'author': 'Trustcode',
    'website': 'http://www.odoo-next.com,br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'base_address_city',
    ],
    'data': [
        'views/res_partner.xml',
    ],
}
