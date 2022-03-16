{  # pylint: disable=C8101,C8103
    'name': 'Odoo Next - Website Address',
    'description': 'Adds fields to address checkout',
    'version': '15.0.1.0.1',
    'category': 'Website',
    'author': 'Trustcode',
    'license': 'OEEL-1',
    'website': 'http://www.odoo-next.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'l10n_br_base_address',
        'website_sale',
    ],
    'data': [
        'views/website_sale_view.xml',
        'views/website_portal.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'l10n_br_website_sale/static/src/js/website_sale.js',
        ]
    }
}
