# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization Base',
    'description': 'Brazilian Localization Base',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://openerpbrasil.org',
    'version': '10.0.1.0.0',
    'depends': [
        'base',
        'sales_team',  #TODO Tentar remover esta dependencia
    ],
    'data': [
        'data/res.state.city.csv',
        'data/l10n_br_base_data.xml',
        'views/br_base.xml',
        'views/ir_module.xml',
        'views/l10n_br_base_view.xml',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'data/l10n_br_base_demo.xml',
    ],
    'test': [
        'test/base_inscr_est_valid.yml',
        'test/base_inscr_est_invalid.yml',
    ],
    'installable': True,
    'auto_install': True,
}
