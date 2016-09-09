# -*- coding: utf-8 -*-
# © 2011  Fabio Negrini - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization CRM Zip',
    'description': """ZIP Search Integration for Brazilian
        Localization of CRM module""",
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'Fabio Negrini - OpenERP Brasil',
    'website': 'http://www.trustcode.com.br',
    'version': '10.0.1.0.0',
    'depends': [
        'l10n_br_zip',
        'l10n_br_crm',
    ],
    'data': [
        'views/crm_lead_view.xml',
        'views/crm_opportunity_view.xml',
    ],
    'test': [
        'test/crm_zip_test.yml'
    ],
    'installable': True,
    'auto_install': True,
}
