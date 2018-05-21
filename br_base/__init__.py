# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import models
from odoo.addons import account
from odoo import api, SUPERUSER_ID


def post_init(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    from odoo.tools import convert_file
    filename = 'data/res.state.city.csv'
    convert_file(cr, 'br_base', filename, None, mode='init',
                 noupdate=True, kind='init', report=None)


_auto_install_l10n_orig = account._auto_install_l10n


def _auto_install_l10n(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    country_code = env.user.company_id.country_id.code
    if country_code and country_code == 'BR':
        module_ids = env['ir.module.module'].search(
            [('name', 'in', ('br_coa_simple',)),
             ('state', '=', 'uninstalled')])
        module_ids.sudo().button_install()
    else:
        _auto_install_l10n_orig(cr, registry)

account._auto_install_l10n = _auto_install_l10n
