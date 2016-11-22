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
        """ Exemplo de retorno
        order_number    SO001
        amount    1600
        checkout_cielo_order_number    708da2506ec44d64aade742c11509459
        created_date    20/09/2015 22:19:36
        customer_name    João Silva
        customer_phone    4898016226
        customer_identity    46317632480
        customer_email    joao_silva0123@gmail.com
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
        payment_method_brand    5
        payment_maskedcreditcard    636368******7691
        payment_installments    1
        payment_status    7
        tid    200920152219370767
        """
        cr, context = request.cr, request.context
        request.registry['payment.transaction'].form_feedback(
            cr, SUPERUSER_ID, post, 'cielo', context=context)

    @http.route('/cielo/retorno/', type='http', auth='none', methods=['POST'])
    def cielo_retorno(self, **post):
        """ Paypal IPN. """
        _logger.info(
            'Beginning Paypal IPN form_feedback with post data %s',
            pprint.pformat(post))  # debug
        self.cielo_validate_data(**post)
        return "<status>OK</status>"

    @http.route(
        '/cielo/notificacao/', type='http', auth="none", methods=['POST'])
    def cielo_notify(self, **post):
        """ Cielo Notify """
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
