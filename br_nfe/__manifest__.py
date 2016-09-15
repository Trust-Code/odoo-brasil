# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Envio de NF-e',
    'summary': """Permite o envio de NF-e através das faturaas do Odoo
    Mantido por Trustcode""",
    'version': '10.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_account_einvoice',
    ],
    'data': [
        'views/account_fiscal_position.xml',
        'views/invoice_eletronic.xml',
        'views/res_company.xml',
        'views/res_partner.xml'
    ],
    'instalable': True,
    'application': True,
}
