# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Odoo Brasil - Módulo Base',
    'description': 'Brazilian Localization Base',
    'version': '10.0.1.0.0',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, OpenERP Brasil',
    'website': 'http://www.trustcode.com,br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
        'Carlos Alberto Cipriano Korovsky <carlos.korovsky@uktech.com.br',
    ],
    'depends': [
        'base', 'web',
    ],
    'external_dependencies': {
        'python': [
            'pytrustnfe.nfe', 'pytrustnfe.certificado'
        ],
    },
    'data': [
        'views/br_base.xml',
        'views/ir_module.xml',
        'views/br_base_view.xml',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'views/res_bank_view.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
    ],
    'test': [
        'test/base_inscr_est_valid.yml',
        'test/base_inscr_est_invalid.yml',
    ],
    'post_init_hook': 'post_init',
    'installable': True,
    'auto_install': True,
}
