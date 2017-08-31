# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Brazilian Localisation Data Extension for Account',
    'description': 'Brazilian Localisation Data Extension for Account',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'br_account',
    ],
    'post_init_hook': 'post_init',
    'category': 'Localisation',
    'installable': True,
    'auto_install': True,
}
