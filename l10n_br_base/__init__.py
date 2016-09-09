# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import models


def post_init(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    from odoo.tools import convert_file
    filename = 'data/res.state.city.csv'
    convert_file(cr, 'l10n_br_base', filename, None, mode='init',
                 noupdate=True, kind='init', report=None)
