# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Integração NFS-e - Provedor DSF',
    'description': "Efetua a integração com o provedor de NFS-e DSF",
    'summary': "Efetua a integração com o provedor de NFS-e DSF",
    'version': '11.0.1.0.0',
    'category': "Accounting & Finance",
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>'
    ],
    'depends': [
        'br_nfse',
    ],
    'data': [
        'data/res.state.city.csv',
        'views/account_fiscal_position.xml',
        'views/account_invoice.xml',
        'views/invoice_eletronic.xml',
        'reports/danfe_dsf.xml',
    ],
}
