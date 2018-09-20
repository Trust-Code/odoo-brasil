# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


{  # pylint: disable=C8101,C8103
    'name': 'Brazilian Localization for Voucher',
    'summary': """Brazilian Localization for Voucher""",
    'description': """Brazilian Localization for Voucher""",
    'version': '11.0.1.0.0',
    'category': 'Localization',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'account_voucher'
    ],
    'data': [
        'data/cron.xml',
        'views/account_voucher.xml',
        'views/account_voucher_line.xml',
    ],
}
