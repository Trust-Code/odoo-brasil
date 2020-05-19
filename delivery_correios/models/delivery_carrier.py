
import re
import requests
from lxml import objectify
from odoo import fields, models


class DeliverCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('correios', 'Correios')])
    service_type = fields.Selection([
        ('04014', 'Sedex'),
        ('04510', 'PAC'),
        ('04782', 'Sedex 12'),
        ('04790', 'Sedex 10'),
        ('04804', 'Sedex Hoje'),
    ], string="Tipo de Entrega")

    def correios_rate_shipment(self, order):
        """ Return the rates for a quotation/SO."""
        origem = re.sub('[^0-9]', '', order.company_id.zip or '')
        destino = re.sub('[^0-9]', '',  order.partner_shipping_id.zip or '')
        total = 0.0
        messages = []
        for line in order.order_line.filtered(lambda x: not x.is_delivery):

            peso = line.product_id.weight
            comprimento = line.product_id.comprimento
            largura = line.product_id.largura
            altura = line.product_id.altura
            servico = self.service_type
            url = "http://ws.correios.com.br/calculador/CalcPrecoPrazo.aspx?\
sCepOrigem={0}&sCepDestino={1}&nVlPeso={2}&nCdFormato=1&\
nVlComprimento={3}&nVlAltura={4}&nVlLargura={5}&\
sCdMaoPropria=n&nVlValorDeclarado=0&sCdAvisoRecebimento=n&\
nCdServico={6}&nVlDiametro=0&StrRetorno=xml&nIndicaCalculo=3".format(
                origem, destino, peso, comprimento, altura, largura, servico
            )
            response = requests.get(url)
            obj = objectify.fromstring(response.text.encode('iso-8859-1'))
            if obj.cServico.Erro == 0:
                total += float(obj.cServico.Valor.text.replace(',', '.'))
            else:
                messages.append(
                    '{0} - {1}'.format(line.product_id.name,
                                       obj.cServico.MsgErro))

        if len(messages) > 0:
            return {
                'success': False,
                'price': 0,
                'error_message': '\n'.join(messages),
            }
        else:
            return {
                'success': True,
                'price': total,
                'warning_message': 'Prazo de entrega',
            }
