# -*- coding: utf-8 -*-
# © 2009  Gabriel C. Stabel
# © 2009  Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    service_type_id = fields.Many2one(
        'l10n_br_account.service.type', u'Tipo de Serviço')
    fiscal_type = fields.Selection(
        [('service', u'Serviço'), ('product', 'Produto')], 'Tipo Fiscal',
        required=True, default='product')
