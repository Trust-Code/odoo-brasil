# © 2009 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    from odoo.tools import convert_file
    filename = 'data/br_account.cfop.csv'
    convert_file(cr, 'br_data_account_product', filename, None,
                 mode='init', noupdate=True, kind='init', report=None)

    filename = 'data/product.fiscal.classification.csv'
    convert_file(cr, 'br_data_account_product', filename, None,
                 mode='init', noupdate=True, kind='init', report=None)
