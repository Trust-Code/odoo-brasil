# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Simples Nacional',
    'summary': """Facilita a emissão de notas fiscais para empresas do Simples -
      Mantido por Trustcode""",
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'l10n_br_nfe',
    ],
    'data': [
        'views/account_tax.xml',
    ],
    'instalable': True,
    'application': True,
}
