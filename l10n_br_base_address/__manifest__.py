{  # pylint: disable=C8101,C8103
    'name': 'Odoo Next - Address Extension',
    'description': 'Modifies address forms',
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
        'l10n_br_base',
        'base_address_city',
    ],
    'data': [
        'data/configuration.xml',
        'data/res.country.csv',
        'data/res.country.state.csv',
        'views/res_partner.xml',
        'views/res_city.xml',
        'views/res_company.xml',
    ],
    'post_init_hook': 'post_init',
}
