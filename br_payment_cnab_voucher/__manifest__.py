# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{   # pylint: disable=C8101,C8103
    'name': "Integração de pagamentos via CNAB 240 - Voucher",
    'summary': """
        Permite enviar pagamentos a fornecedores via integração bancária
        (CNAB 240) - Mantido por Trustcode""",
    'description': """
        Permite enviar pagamentos a fornecedores via integração bancária
        (CNAB 240) - Mantido por Trustcode""",
    'author': "Trustcode",
    'website': "http://www.trustcode.com.br",
    'category': 'account',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'contributors': [
        'Marina Domingues <mgd.marinadomingues@gmail.com>'
        'Felipe Paloschi <paloschi.eca@gmail.com>',
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'account_voucher',
        'br_payment_cnab',
    ],
    'data': [
        'views/account_voucher.xml',
        'views/payment_order.xml',
    ],
    'auto_install': True
}
