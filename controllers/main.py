# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CieloController(http.Controller):
    _notify_url = '/cielo/notificacao/'
    _status_url = '/cielo/status/'

    @http.route(
        '/cielo/notificacao/', type='http', auth="none",
        methods=['GET', 'POST'], csrf=False)
    def cielo_notify(self, **post):
        """ Cielo Notificação"""
        _logger.info(u'Iniciando retorno de notificação cielo post-data: %s',
                     pprint.pformat(post))

        request.env['payment.transaction'].sudo().form_feedback(post, 'cielo')
        return "<status>OK</status>"

    @http.route('/cielo/status/', type='http', auth="none",
                methods=['GET', 'POST'], csrf=False)
    def cielo_status(self, **post):
        """ Quando o status de uma transação modifica essa url é chamada
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
        _logger.info(
            u'Iniciando mudança de status de transação post-data: %s',
            pprint.pformat(post))  # debug
        self.cielo_validate_data(**post)
        return "<status>OK</status>"
