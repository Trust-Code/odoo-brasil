# Copyright (C) 2020 - Carlos R. Silveira - ATSti Soluções
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Sped EFD ICMS/IPI',
    'summary': """ Gera arquivo Sped EFD ICMS/IPI""",
    'version': '1.0',
    'category': 'Localisation',
    'author': 'ATSti Solucoes',
    'website': 'http://www.atsti.com.br',
    'license': 'AGPL-3',
    'contributors': [
        'Carlos R. Silveira<carlos@atsti.com.br>',
    ],
    'depends': [
        'br_account_einvoice',
        'br_sped_base',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sped_icms_ipi_view.xml',
    ],
    'demo': [],
    'installable': True,
}
