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
    def cielo_form_generate_values(self, tx_values):
        """ Função para gerar HTML POST da Cielo """
        total_desconto = 0
        items = [{
            "Name": "Pagamento pedido: %s" % tx_values['reference'],
            "Description": "Pagamento pedido: %s" % tx_values['reference'],
            "UnitPrice": "%d" % round(tx_values['amount'] * 100),
            "Quantity": '1',
            "Type": 'Service',
        }]
        address = {
            "Street": tx_values['partner'].street,
            "Number": tx_values['partner'].number,
            "Complement": tx_values['partner'].street2,
            "District": tx_values['partner'].district,
            "City": tx_values['partner'].city_id.name,
            "State": tx_values['partner'].state_id.code,
        }
        if len(tx_values['partner'].street2 or '') > 0:
            address['Complement'] = tx_values['partner'].street2
        payment = {"BoletoDiscount": 0, "DebitDiscount": 0}
        customer = {
            "FullName": tx_values['partner'].name,
            "Email": tx_values['partner'].email,
        }
        cnpj_cpf = re.sub('[^0-9]', '', tx_values['partner'].cnpj_cpf or '')
        phone = re.sub('[^0-9]', '', tx_values['partner'].phone or '')
        if len(cnpj_cpf) in (11, 14):
            customer['Identity'] = cnpj_cpf
        if len(phone) == 11:
            customer['Phone'] = phone

        shipping = {
            "Type": "WithoutShipping",
            "TargetZipCode": re.sub(
                '[^0-9]', '', tx_values['partner'].zip or ''),
            "Address": address,
        }
        total_desconto *= 100
        discount = {'Type': 'Amount', 'Value': int(total_desconto)}
        options = {"AntifraudEnabled": False, "ReturnUrl": self.return_url}
        order_json = {
            "OrderNumber": tx_values['reference'],
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
