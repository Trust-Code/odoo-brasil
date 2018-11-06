# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{   # pylint: disable=C8101,C8103
    'name': "Integração de pagamentos via CNAB 240",
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
        'Guilherme Lenon da Silva <guilhermelds@gmail.com>',
        'Marina Domingues <mgd.marinadomingues@gmail.com>'
        'Felipe Paloschi <paloschi.eca@gmail.com>',
    ],
    'depends': [
        'account_invoicing',
        'br_account_payment',
        'br_account_voucher',
        'br_cnab'
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/payment_mode.xml',
        'views/payment_information.xml',
        'views/payment_order.xml',
        'views/res_config_settings.xml',
        'wizard/payment_cnab_import.xml',
        'wizard/manual_reconcile.xml',
        'wizard/approve_payments.xml',
    ],
    'application': True,
}
