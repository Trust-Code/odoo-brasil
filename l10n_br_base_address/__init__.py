from . import models


def post_init(cr, registry):
    from odoo.tools import convert_file
    filename = 'data/res.city.csv'
    convert_file(cr, 'l10n_br_base_address', filename, None, mode='init',
                 noupdate=True, kind='init')
