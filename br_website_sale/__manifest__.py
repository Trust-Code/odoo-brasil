# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Website Sale Checkout Fields for Brazil',
    'summary': """Adds fields to e-commerce checkout""",
    'description': 'Website Sale Checkout Fields for Brazil',
    'version': '10.0.1.0.0',
    'category': 'Website',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'br_base', 'br_zip', 'website_sale'
    ],
    'data': [
        'views/website_sale_view.xml',
        'views/website_portal.xml',
    ],
    'installable': True,
}
