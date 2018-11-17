# © 2018 Carlos R. Silveira, ATSti
# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Sped EFD - ICMS/IPI',
    'version': '11.0.1.0.0',
    'category': 'Localisation',
    'author': 'ATSti Solucoes',
    'website': 'http://www.atsti.com.br',
    'license': 'AGPL-3',
    'contributors': [
        'Carlos Silveira <carlos@atsti.com.br>',
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_account',
        'product',
    ],
    'data': [
        'views/product_view.xml',
        'views/sped_view.xml',
        'views/sped_efd_view.xml',
    ],
}
