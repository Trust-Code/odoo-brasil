# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Brazilian Localisation Data Extension for Base',
    'description': 'Brazilian Localisation Data Extension for Base',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'version': '10.0.1.0.0',
    'depends': [
        'br_base',
    ],
    'data': [
        'data/res.bank.csv',
        'data/res.country.csv',
        'data/res.country.state.csv',
        'data/br_base_data.xml',
    ],
    'demo': [],
    'category': 'Localisation',
    'installable': True,
    'auto_install': True,
}
