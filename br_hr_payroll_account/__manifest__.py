# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazil - Payroll with Accounting',
    'category': 'Localization',
    'depends': ['br_hr_payroll', 'hr_payroll_account', 'br_coa'],
    'data': [
        'data/br_hr_payroll_account_data.xml',
    ],
    'post_init_hook': '_set_accounts',
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
    'maintainer': 'Trustcode',
    'website': 'http://www.trustcode.com.br',
}
