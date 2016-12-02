# -*- coding: utf-8 -*-
# © 2009  Gabriel C. Stabel
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields
from .cst import ORIGEM_PROD


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_type = fields.Selection(
        [('service', u'Serviço'), ('product', 'Produto')], 'Tipo Fiscal',
        required=True, default='product')

    origin = fields.Selection(ORIGEM_PROD, 'Origem', default='0')

    fiscal_classification_id = fields.Many2one(
        'product.fiscal.classification', string="Classificação Fiscal (NCM)")

    service_type_id = fields.Many2one(
        'br_account.service.type', u'Tipo de Serviço')

    cest = fields.Char(string="CEST", size=10,
                       help="Código Especificador da Substituição Tributária")
