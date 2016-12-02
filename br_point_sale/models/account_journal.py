#!/usr/bin/env python
# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


metodos = [
    ('01', u'Dinheiro'),
    ('02', u'Cheque'),
    ('03', u'Cartão de Crédito'),
    ('04', u'Cartão de Débito'),
    ('05', u'Crédito Loja'),
    ('10', u'Vale Alimentacão'),
    ('11', u'Vale Presente'),
    ('13', u'Vale Combustível'),
    ('99', u'Outros'),
]


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    metodo_pagamento = fields.Selection(metodos, string='Método de Pagamento')
