from . import models
from . import wizard


def post_init(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    from odoo.tools import convert_file

    filename = 'data/account.ncm.csv'
    convert_file(cr, 'l10n_br_account', filename, None,
                 mode='init', noupdate=True, kind='init')
