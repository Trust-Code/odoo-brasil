# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localisation Data Extension for Account',
    'description': 'Brazilian Localisation Data Extension for Account',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '7.0',
    'depends': [
        'l10n_br_account_new',
    ],
    'data': [
        'l10n_br_account.cnae.csv',
        'l10n_br_account.service.type.csv',
    ],
    'category': 'Localisation',
    'installable': True,
    'auto_install': True,
}
