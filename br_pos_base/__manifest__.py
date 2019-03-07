# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{   # pylint: disable=C8101,C8103
    'name': 'Point of Sale - Customer Modifications',
    'summary': """Module to adapt Odoo Point of Sale to Brazil""",
    'description': 'Point of Sale Brazil',
    'version': '11.0.1.0.0',
    'category': 'pos',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'point_of_sale',
        'br_zip',
    ],
    'data': [
        'views/pos_templates.xml',
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
    'auto_install': True,
}
