# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import json
import logging
import requests

from odoo import api, models, fields
from odoo.http import request
from datetime import datetime

_logger = logging.getLogger(__name__)

odoo_request = request


class AcquirerCielo(models.Model):
    _inherit = 'payment.acquirer'

    def _default_return_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return "%s%s" % (base_url, '/shop/confirmation')

    provider = fields.Selection(selection_add=[('cielo', 'Cielo')])
    cielo_merchant_id = fields.Char(string='Cielo Merchant Id')
    return_url = fields.Char(string="Url de Retorno",
                             default=_default_return_url, size=300)

    @api.multi
    def cielo_form_generate_values(self, values):
        """ Função para gerar HTML POST da Cielo """
        order = odoo_request.website.sale_get_order()
        if not order or not order.payment_tx_id:
            return {
                'checkout_url': '/shop/payment',
            }

        total_desconto = 0
        items = []
        for line in order.order_line:
            if line.product_id.fiscal_type == 'service':
                tipo = 'Service'
            elif line.product_id.fiscal_type == 'product':
                tipo = 'Asset'
            else:
                tipo = 'Payment'
            total_desconto += line.discount
            item = {
                "Name": line.product_id.name,
                "Description": line.name,
                "UnitPrice": "%d" % round(line.price_unit * 100),
                "Quantity": "%d" % line.product_uom_qty,
                "Type": tipo,
            }
            if line.product_id.default_code:
                item["Sku"] = line.product_id.default_code
            if line.product_id.weight:
                item['Weight'] = "%d" % (line.product_id.weight * 1000)
            items.append(item)
        shipping = {
            "Type": "WithoutShipping",
            "TargetZipCode": re.sub('[^0-9]', '', order.partner_id.zip),
        }
        address = {
            "Street": order.partner_id.street,
            "Number": order.partner_id.number,
            "Complement": order.partner_id.street2,
            "District": order.partner_id.district,
            "City": order.partner_id.city_id.name,
            "State": order.partner_id.state_id.code,
        }
        if len(order.partner_id.street2) > 0:
            address['Complement'] = order.partner_id.street2
        payment = {"BoletoDiscount": 0, "DebitDiscount": 0}
        customer = {
            "Identity": re.sub('[^0-9]', '', order.partner_id.cnpj_cpf or ''),
            "FullName": order.partner_id.name,
            "Email": order.partner_id.email,
            "Phone": re.sub('[^0-9]', '', order.partner_id.phone or ''),
        }
        total_desconto *= 100
        discount = {'Type': 'Amount', 'Value': int(total_desconto)}
        options = {"AntifraudEnabled": False, "ReturnUrl": self.return_url}
        order_json = {
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
        json_send = json.dumps(order_json)
        headers = {"Content-Type": "application/json",
                   "MerchantId": self.cielo_merchant_id}
        request_post = requests.post(
            "https://cieloecommerce.cielo.com.br/api/public/v1/orders",
            data=json_send, headers=headers, verify=False)
        response = request_post.text
        resposta = json.loads(response)
        if "message" in resposta:
            request.session.update({
                'sale_transaction_id': False,
            })
            _logger.error(resposta)
            raise Exception("Erro ao comunicar com a CIELO")

        return {
            'checkout_url': resposta["settings"]["checkoutUrl"],
        }


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

    @api.model
    def _cielo_form_get_tx_from_data(self, data):
        reference = data.get('order_number')
        txs = self.env['payment.transaction'].search(
            [('reference', '=', reference)])
        return txs[0]

    @api.multi
    def _cielo_form_validate(self, data):
        reference = data.get('order_number')
        txn_id = data.get('checkout_cielo_order_number')
        cielo_id = data.get('tid', False)
        payment_type = data.get('payment_method_type')
        amount = float(data.get('amount', '0')) / 100.0
        state_cielo = data.get('payment_status')

        # 1 - Pendente (Para todos os meios de pagamento)
        # 2 - Pago (Para todos os meios de pagamento)
        # 3 - Negado (Somente para Cartão Crédito)
        # 4 - Expirado (Cartões de Crédito e Boleto)
        # 5 - Cancelado (Para cartões de crédito)
        # 6 - Não Finalizado (Todos os meios de pagamento)
        # 7 - Autorizado (somente para Cartão de Crédito)
        # 8 - Chargeback (somente para Cartão de Crédito)
        state = 'pending' if state_cielo == '1' else 'error'
        state = 'done' if state_cielo in ('2', '7') else state

        values = {
            'reference': reference,
            'amount': amount,
            'acquirer_reference': txn_id,
            'state': state,
            'date_validate': datetime.now(),
            'transaction_type': payment_type,
            'cielo_transaction_id': cielo_id,
            'payment_installments': data.get('payment_installments', False),
            'payment_boletonumber': data.get('payment_boletonumber', False),
            'payment_method_brand': data.get('payment_method_brand', False),
            'state_cielo': state_cielo
        }
        res = {}
        res.update({k: v for k, v in values.items() if v})
        return self.write(res)
