# -*- coding: utf-8 -*-


from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'   

    l10n_br_operation = fields.Char(
        string='Natureza Operação',
        help=u'Este registro tem por objetivo codificar os textos das \
            diferentes naturezas da operação/prestações discriminadas \
            nos documentos fiscais. Esta codificação e suas descrições \
            são livremente criadas e mantidas pelo contribuinte.')
