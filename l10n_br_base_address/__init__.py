from . import models


def post_init(env):
    from odoo.tools import convert_file
    filename = 'data/res.city.csv'
    convert_file(env, 'l10n_br_base_address', filename, None, mode='init',
                 noupdate=True, kind='init')
