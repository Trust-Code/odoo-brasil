# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015 Trustcode - www.trustcode.com.br                         #
#              Danimar Ribeiro <danimaribeiro@gmail.com>                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

import logging

from odoo import api, models, fields
from odoo.http import request
from datetime import datetime
from urllib2 import Request, urlopen
from json import dumps

_logger = logging.getLogger(__name__)

odoo_request = request


class AcquirerCielo(models.Model):
    _inherit = 'payment.acquirer'

    cielo_merchant_id = fields.Char(string='Cielo Merchant Id')

    @api.multi
    def cielo_form_generate_values(self, values):
        """ Função para gerar HTML POST da Cielo """
        order = odoo_request.website.sale_get_order()
        total_desconto = 0
        items = []
        for line in order.order_line:
            if line.product_id.type == 'service':
                tipo = 'Service'
            elif line.product_id.type in ['consu', 'product']:
                tipo = 'Asset'
            else:
                tipo = 'Payment'
            total_desconto += line.discount
            item = {
                "Name": line.product_id.name,
                "Description": line.name,
                "UnitPrice": line.price_unit,
                "Quantity": line.product_uom_qty,
                "Type": tipo,
                "Sku": line.product_id.default_code,
            }
            if line.product_id.weight:
                item['Weight'] = line.product_id.weight
            items.append(item)
        service = {"Name": "Grátis", "Price": 0}
        shipping = {"Type": "Free", "Services": service}
        address = {
            "Street": order.partner_id.street,
            "Number": order.partner_id.number,
            "District": order.partner_id.district,
            "City": order.partner_id.city_id.name,
            "State": order.partner_id.state_id.name,
        }
        if (order.partner_id.street2) > 0:
            address['Complement'] = order.partner_id.street2
        payment = {"BoletoDiscount": 0, "DebitDiscount": 0}
        customer = {
            "Identity": order.partner_id.cnpj_cpf,
            "FullName": order.partner_id.name,
            "Email": order.partner_id.email,
            "Phone": order.partner_id.phone,
        }
        total_desconto *= 100
        discount = {'Type': 'Amount', 'Value': int(total_desconto)}
        options = {"AntifraudEnabled": False}
        order_jason = {
            "OrderNumber": values['reference'],
            "SoftDescriptor": "FOOBARBAZ",
            "Cart": {
                "Discount": discount,
                "Items": items,
            },
            "Shipping": shipping,
            "Payment": payment,
            "Customer": customer,
            "Options": options,
        }
        json = dumps(order_jason)
        headers = {"Content-Type": "application/json",
                   "MerchantId": "00000000-0000-0000-0000-000000000000"}
        request = Request(
            "https://cieloecommerce.cielo.com.br/api/public/v1/orders",
            data=json, headers=headers)
        response = urlopen(request).read()
        print response


class TransactionCielo(models.Model):
    _inherit = 'payment.transaction'

    cielo_transaction_id = fields.Char(string=u'ID Transação')
    state_cielo = fields.Selection(
        [('1', u'Pendente'), ('2', u'Pago'), ('3', u'Negado'),
         ('5', u'Cancelado'), ('6', u'Não Finalizado'), ('7', u'Autorizado')],
        string=u"Situação Cielo")
    transaction_type = fields.Selection(
        [('1', u'Cartão de Crédito'), ('2', u'Boleto Bancário'),
         ('3', u'Débito Online'), ('4', u'Cartão de Débito')],
        string=u'Tipo pagamento')
    payment_installments = fields.Integer(u'Número de parcelas')
    payment_method_brand = fields.Selection(
        [('1', u'Visa'), ('2', u'Mastercard'), ('3', u'American Express'),
         ('4', u'Diners'), ('5', u'Elo'), ('6', u'Aura'), ('7', u'JCB')],
        string=u"Bandeira Cartão")
    payment_boletonumber = fields.Char(string=u"Número boleto", size=100)

    url_cielo = fields.Char(
        string=u"Cielo", size=60,
        default="https://www.cielo.com.br/VOL/areaProtegida/index.jsp")

    def _cielo_form_get_tx_from_data(self, cr, uid, data, context=None):
        acquirer_id = self.pool['payment.acquirer'].search(
            cr, uid, [('provider', '=', 'cielo')], context=context)
        acquirer = self.pool['payment.acquirer'].browse(
            cr, uid, acquirer_id, context=context)

        reference = data.get('order_number')
        txn_id = data.get('checkout_cielo_order_number')
        cielo_id = data.get('tid')
        payment_type = data.get('payment_method_type')
        amount = float(data.get('amount')) / 100.0
        state_cielo = data.get('payment_status')

        sale_id = self.pool['sale.order'].search(
            cr, uid, [('name', '=', reference)], context=context)
        sale_order = self.pool['sale.order'].browse(
            cr, uid, sale_id, context=context)
        state = 'pending' if state_cielo == '1' else 'done'

        values = {
            'reference': reference,
            'amount': amount,
            'currency_id': acquirer.company_id.currency_id.id,
            'acquirer_id': acquirer.id,
            'acquirer_reference': txn_id,
            'partner_name': sale_order.partner_id.name,
            'partner_address': sale_order.partner_id.street,
            'partner_email': sale_order.partner_id.email,
            'partner_lang': sale_order.partner_id.lang,
            'partner_zip': sale_order.partner_id.zip,
            'partner_city': sale_order.partner_id.l10n_br_city_id.name,
            'partner_country_id': sale_order.partner_id.country_id.id,
            'state': state,
            'partner_id': sale_order.partner_id.id,
            'date_validate': datetime.now(),
            'transaction_type': payment_type,
            'cielo_transaction_id': cielo_id,
            'payment_installments': int(data.get('payment_installments', '1')),
            'payment_boletonumber': data.get('payment_boletonumber', ''),
            'payment_method_brand': data.get('payment_method_brand', None),
            'state_cielo': state_cielo
        }

        payment_id = self.create(cr, uid, values, context=context)
        return self.browse(cr, uid, payment_id, context=context)
