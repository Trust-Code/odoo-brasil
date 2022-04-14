# © 2021 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.


{
    'name': 'Integração Banco Itau - Boleto Bancário',
    'version': '13.0.1.0.1',
    'category': 'Finance',
    'sequence': 5,
    'author': 'Trustcode',
    'license': 'OPL-1',
    'summary': """Realiza a integração com Boleto Bancário no Banco Itau-
    Created by Trustcode""",
    'website': 'https://www.trustcode.com.br',
    'support': 'vendas@trustcode.com.br',
    'price': '50',
    'currency': 'EUR',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'l10n_br_automated_payment',
        'l10n_br_eletronic_document',
    ],
    'data': [
        'data/acquirer.xml',
    ],
    'application': True,
}
