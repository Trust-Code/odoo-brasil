# -*- coding: utf-8 -*-
# © 2013 Renato Lima - Akretion
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    indPag = fields.Selection(
        [('0', u'Pagamento à Vista'), ('1', u'Pagamento à Prazo'),
         ('2', 'Outros')], 'Indicador de Pagamento', default='1')


class AccountTax(models.Model):
    """Implement computation method in taxes"""
    _inherit = 'account.tax'

    @api.v7
    def compute_all(self, cr, uid, ids, price_unit, currency_id=None,
                    quantity=1.0, product_id=None, partner_id=None,
                    context=None):
        return super(AccountTax, self).compute_all(cr, uid, ids, price_unit,
                                                   currency_id, quantity,
                                                   product_id, partner_id,
                                                   context=context)

    @api.v8
    def compute_all(self, price_unit, currency=None, quantity=1.0,
                    product=None, partner=None):
        return super(AccountTax, self).compute_all(price_unit, currency,
                                                   quantity, product, partner)
