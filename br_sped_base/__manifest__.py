# © 2019 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Base Sped Brasil',
    'summary': """Validação e campos extras para geração do SPED
    Mantido por Trustcode""",
    'description': 'Base Sped Brasil',
    'version': '12.0.1.0.0',
    'sequence': 2,
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_nfe',
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product.xml',
    ],
    'application': True,
}
