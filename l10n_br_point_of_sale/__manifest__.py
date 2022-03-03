# © 2020 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'NFC-e - Point of Sale Brazil',
    'summary': """Module to adapt Odoo Point of Sale to Brazil""",
    'description': 'Point of Sale Brazil',
    'version': '13.0.1.0.0',
    'category': 'pos',
    'author': 'Trustcode',
    'license': 'Other OSI approved licence',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'point_of_sale',
        'l10n_br_eletronic_document',
    ],
    'external_dependencies': {
        'python': [
            'pytrustnfe',
        ],
    },
    'data': [
        'views/account_journal.xml',
        'views/pos_order.xml',
        'views/invoice_eletronic.xml',
        'views/pos_payment_method.xml',
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'https://cdnjs.cloudflare.com/ajax/libs/jquery.mask/1.14.10/jquery.mask.js',
            'l10n_br_point_of_sale/static/src/lib/print.min.js',
            'l10n_br_point_of_sale/static/src/js/main.js',
            'l10n_br_point_of_sale/static/src/js/models.js',
            'l10n_br_point_of_sale/static/src/js/screens.js',
        ],
        'point_of_sale.pos_assets_backend_style': [
            'l10n_br_point_of_sale/static/src/lib/print.min.css',
        ]
    },
    'application': True,
    'installable': True
}
