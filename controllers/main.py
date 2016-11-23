# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import logging
import pprint

from odoo import http, SUPERUSER_ID
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteSale(WebsiteSale):

    def checkout_form_validate(self, mode, all_form_values, data):
        error = super(WebsiteSale, self).checkout_form_validate(
            mode, all_form_values, data)
        return error


class CieloController(http.Controller):
    _return_url = '/cielo/retorno/'
    _notify_url = '/cielo/notificacao/'
    _status_url = '/cielo/status/'

    def cielo_validate_data(self, **post):
        """ Parametros de retorno Cielo
        checkout_cielo_order_number    708da2506ec44d64aade742c11509459
        amount    1600
        order_number    SO001
        created_date    20/09/2015 22:19:36
        customer_name    João Silva
        customer_phone    4898016226
        customer_identity    46317632480
        customer_email    joao_silva0123@gmail.com
        customer_phone   48999998888
        discount_amount  0000
        shipping_type    2
        shipping_name    Servico da Loja
        shipping_price    500
        shipping_address_zipcode    88032050
        shipping_address_district    Saco Grande
        shipping_address_city    Florianópolis
        shipping_address_state    SC
        shipping_address_line1    Rua Donícia Maria da Costa
        shipping_address_line2    ap02
        shipping_address_number    83
        payment_method_type    1
            1 - Cartão de Crédito
            2 - Boleto Bancário
            3 - Débito Online
            4 - Cartão de Débito
        payment_method_bank    1
            1 - Banco do Brasil
            2 - Bradesco
        payment_method_brand    1
            1 - Visa
            2 - Mastercad
            3 - AmericanExpress
            4 - Diners
            5 - Elo
            6 - Aura
            7 - JCB
        payment_maskedcreditcard    636368******7691
        payment_installments    1
        payment_boletonumber 222222
        payment_boletoexpirationdate  22052016
        payment_antifrauderesult 1
        payment_status    7
        tid    200920152219370767
        """
        cr, context = request.cr, request.context
        request.registry['payment.transaction'].form_feedback(
            cr, SUPERUSER_ID, post, 'cielo', context=context)

    @http.route(
        '/cielo/notificacao/', type='http', auth="none", methods=['POST'])
    def cielo_notify(self, **post):
        """ Cielo Notificação - Parametros
        checkout_cielo_order_number 708da2506ec44d64aade742c11509459
        amount 1600
        order_number SO00
        payment_status 1
            1 - Pendente (Para todos os meios de pagamento)
            2 - Pago (Para todos os meios de pagamento)
            3 - Negado (Somente para Cartão Crédito)
            4 - Expirado (Cartões de Crédito e Boleto)
            5 - Cancelado (Para cartões de crédito)
            6 - Não Finalizado (Todos os meios de pagamento)
            7 - Autorizado (somente para Cartão de Crédito)
            8 - Chargeback (somente para Cartão de Crédito)
        """
        _logger.info('Iniciando retorno de notificação cielo post-data: %s',
                     pprint.pformat(post))

        self.cielo_validate_data(**post)
        return "<status>OK</status>"

    @http.route('/cielo/status/', type='http', auth="none")
    def cielo_cancel(self, **post):
        """ Quando o status de uma transação modifica essa url é chamada """
        _logger.info(
            'Iniciando mudança de status de transação post-data: %s',
            pprint.pformat(post))  # debug

        return "<status>OK</status>"
