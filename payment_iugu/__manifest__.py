{
    'name': "Método de Pagamento Iugu",
    'summary': "Payment Acquirer: Iugu Implementation",
    'description': """Iugu payment gateway for Odoo.""",
    'author': "Trustcode",
    'category': 'Accounting',
    'version': '11.0.0',
    'depends': ['account', 'payment', 'sale'],
    'external_dependencies': {
        'python': ['iugu'],
    },
    'data': [
        'views/payment_views.xml',
        'views/iugu.xml',
        'data/iugu.xml',
    ],
    'installable': True,
}
