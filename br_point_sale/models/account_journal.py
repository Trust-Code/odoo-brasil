#!/usr/bin/env python
# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


metodos = [
    ('01', 'Dinheiro'),
    ('02', 'Cheque'),
    ('03', 'Cartão de Crédito'),
    ('04', 'Cartão de Débito'),
    ('05', 'Crédito Loja'),
    ('10', 'Vale Alimentacão'),
    ('11', 'Vale Presente'),
    ('13', 'Vale Combustível'),
    ('99', 'Outros'),
]


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    metodo_pagamento = fields.Selection(metodos, string='Método de Pagamento')
