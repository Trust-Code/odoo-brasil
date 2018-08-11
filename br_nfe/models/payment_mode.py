# -*- coding: utf-8 -*-
# © 2018 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    tipo_pagamento = fields.Selection(
        [('01', u'Dinheiro'),
         ('02', u'Cheque'),
         ('03', u'Catão de Crédito'),
         ('04', u'Cartão de Débito'),
         ('05', u'Crédito Loja'),
         ('10', u'Vale Alimentação'),
         ('11', u'Vale Refeição'),
         ('12', u'Vale Presente'),
         ('13', u'Vale Combustível'),
         ('14', u'Duplicata Mercantil'),
         ('90', u'Sem pagamento'),
         ('99', u'Outros')],
        string=u"Forma de Pagamento", default="14")
