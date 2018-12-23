{
    'name': 'POS NFC-e',
    'summary': 'Esse modulo foi desenvolvido para emitir NFC-e via POS',
    'author': "Implanti Soluções",
    'website': "http://www.implanti.com.br",
    'category': 'Point Of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'point_of_sale',
        'br_account_einvoice',
        'br_nfe',
    ],
    # always loaded
    'data': [
        'views/header.xml'
    ],
    'qweb': ['static/src/xml/pos.xml']
}
