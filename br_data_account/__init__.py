# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    from odoo.tools import convert_file
    filename = 'data/br_account.cnae.csv'
    convert_file(cr, 'br_data_account', filename, None, mode='init',
                 noupdate=True, kind='init', report=None)

    filename = 'data/br_account.service.type.csv'
    convert_file(cr, 'br_data_account', filename, None, mode='init',
                 noupdate=True, kind='init', report=None)

    filename = 'data/br_account.fiscal.document.csv'
    convert_file(cr, 'br_data_account', filename, None, mode='init',
                 noupdate=True, kind='init', report=None)
