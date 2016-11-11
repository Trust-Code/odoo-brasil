# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Simples Nacional',
    'summary': """Facilita a emissão de notas fiscais para empresas do Simples -
      Mantido por Trustcode""",
    'description': 'Simples Nacional',
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_sale',
    ],
    'data': [
        'data/br_simples_nacional.xml',
        'views/account_invoice.xml',
        'views/account_fiscal_position.xml',
    ],
    'instalable': True,
    'application': True,
}
