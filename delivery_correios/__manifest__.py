{  # pylint: disable=C8101,C8103
    'name': 'Odoo Next - Correios Integration',
    'description': 'Integrate e-commerce to correios',
    'version': '11.0.1.0.0',
    'category': 'Website',
    'author': 'Trustcode',
    'license': 'LGPL-3',
    'website': 'http://www.odoo-next.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'br_delivery',
        'website_sale',
    ],
    'data': [
        'views/delivery.xml',
    ],
}
