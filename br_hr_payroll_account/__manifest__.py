# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Folha de Pagamento Brasil',
    'description': 'Folha de Pagamento Brasil',
    'maintainer': 'Trustcode',
    'website': 'http://www.trustcode.com.br',
    'license': 'AGPL-3',
    'category': 'Localization',
    'depends': ['br_hr_payroll', 'hr_payroll_account'],
    'data': [
        'data/br_hr_payroll_account_data.xml',
    ],
    'post_init_hook': '_set_accounts',
    'installable': True,
    'application': False,
}
