# © 2020 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import re
import base64
import zeep
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from requests.exceptions import ConnectionError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    has_contract = fields.Boolean(string="Tem Contrato?")
    correio_login = fields.Char(string=u"Login Correios", size=30)
    correio_password = fields.Char(string=u"Senha do Correio", size=30)
    cod_administrativo = fields.Char(string=u"Código Administrativo", size=20)
    num_contrato = fields.Char(string=u"Número de Contrato", size=20)
    cartao_postagem = fields.Char(
        string=u"Número do cartão de Postagem", size=20
    )

    delivery_type = fields.Selection(
        selection_add=[("correios", u"Correios")]
    )
    # Type without contract
    service_type = fields.Selection(
        [
            ("04014", "Sedex"),
            ("04510", "PAC"),
            ("04782", "Sedex 12"),
            ("04790", "Sedex 10"),
            ("04804", "Sedex Hoje"),
        ],
        string="Tipo de Entrega",
        help="Tipo de entrega utilizado quando a empresa não possui contrato \
com o Correio",
    )
    # Type for those who have contract
    service_id = fields.Many2one(
        "delivery.correios.service", string="Serviço"
    )
    mao_propria = fields.Selection(
        [("S", "Sim"), ("N", "Não")], string="Entregar em Mão Própria"
    )
    valor_declarado = fields.Boolean("Valor Declarado")
    aviso_recebimento = fields.Selection(
        [("S", "Sim"), ("N", "Não")], string="Receber Aviso de Entrega"
    )
    ambiente = fields.Selection(
        [("1", "Homologação"), ("2", "Produção")],
        default="1",
        string="Ambiente",
    )

    @api.onchange("has_contract")
    def onchange_contract(self):
        if self.has_contract:
            self.integration_level = "rate_and_ship"
        else:
            self.integration_level = "rate"

    def get_correio_sigep(self):
        sigep = self.env["correios.sigep"].search(
            [
                ("login", "=", self.correio_login),
                ("environment", "=", self.ambiente),
            ]
        )
        if not sigep:
            sigep = self.env["correios.sigep"].create(
                {
                    "login": self.correio_login,
                    "password": self.correio_password,
                    "environment": self.ambiente,
                }
            )
        return sigep

    def action_get_correio_services(self):
        client = self.get_correio_sigep()
        result = client.busca_cliente(self.num_contrato, self.cartao_postagem)
        servicos = result["contratos"][0]["cartoesPostagem"][0]["servicos"]
        ano_assinatura = result["contratos"][0]["dataVigenciaInicio"]
        for item in servicos:
            correio = self.env["delivery.correios.service"]
            item_correio = correio.search([("code", "=", item["codigo"])])
            chancela = item["servicoSigep"]["chancela"]

            image_chancela = chancela and chancela.get("chancela")
            if image_chancela:
                image_chancela = base64.b64encode(image_chancela)
            vals = {
                "code": item["codigo"].strip(),
                "identifier": item["id"],
                "chancela": image_chancela,
                "name": item["descricao"].strip(),
                "delivery_id": self.id,
                "ano_assinatura": str(ano_assinatura)[:4],
            }
            if item_correio:
                item_correio.write(vals)
            else:
                correio.create(vals)

    def _get_common_price_parameters(self, origem, destino):
        codigo_servico = self.service_id.code or self.service_type
        if not codigo_servico:
            raise UserError(
                "Configure o codigo de servico (Correios) no método de entrega"
            )

        params = {
            "numero_servico": codigo_servico,
            "valor_declarado": 0,
            "aviso_recebimento": False,
            "mao_propria": False,
            "formato": 1,
            "cep_origem": origem,
            "cep_destino": destino,
            "diametro": str(0),
        }

        if self.cod_administrativo and self.correio_password:
            params.update(
                {
                    "cod_administrativo": self.cod_administrativo,
                    "senha": self.correio_password,
                }
            )

        return params

    def _get_price_params_per_line(self, origem, destino, lines):
        params_list = []
        common_params = self._get_common_price_parameters(origem, destino)
        for line in lines:
            params = common_params.copy()
            comprimento = line.product_id.comprimento
            altura = line.product_id.altura
            largura = line.product_id.largura
            weight = line.product_id.weight
            params.update(
                {
                    "peso": str(weight if weight > 0.3 else 0.3),
                    "comprimento": str(
                        comprimento if comprimento > 16 else 16
                    ),
                    "altura": str(altura if altura > 2 else 2),
                    "largura": str(largura if largura > 11 else 11),
                }
            )
            params_list.append([line.product_id.name, params])
        return params_list

    def _get_price_params_per_packaging(
        self, origem, destino, packaging, weight
    ):

        params = self._get_common_price_parameters(origem, destino)

        comprimento = packaging.length
        altura = packaging.height
        largura = packaging.width
        params.update(
            {
                "peso": str(weight if weight > 0.3 else 0.3),
                "comprimento": str(comprimento if comprimento > 16 else 16),
                "altura": str(altura if altura > 2 else 2),
                "largura": str(largura if largura > 11 else 11),
            }
        )
        return [[packaging.name, params]]

    def _get_normal_shipping_rate(self, order):
        origem = re.sub("[^0-9]", "", order.company_id.zip or "")
        destino = re.sub("[^0-9]", "", order.partner_shipping_id.zip or "")
        total = 0.0
        messages = []

        order_lines = order.order_line.filtered(lambda x: not x.is_delivery)

        packaging_id = self.env["product.packaging"].browse(
            self.env.context.get("default_packaging_id")
        )
        if packaging_id:
            params_list = self._get_price_params_per_packaging(
                origem,
                destino,
                packaging_id,
                sum(
                    line.product_id.weight * line.product_uom_qty
                    for line in order_lines
                ),
            )

        else:
            params_list = self._get_price_params_per_line(
                origem, destino, order_lines
            )

        for name, params in params_list:

            try:
                data = self.get_correio_sigep().calcular_preco_prazo(**params)
            except ConnectionError:
                messages.append(
                    "Não foi possível calcular o frete, tente novamente!"
                )
                continue

            if data.get("Erro") == "0":
                total += float(data.get("Valor").replace(",", "."))
            elif data.get("Erro") == "-888":
                messages.append("Serviço indisponível para o CEP de destino!")
            else:
                messages.append("{0} - {1}".format(name, data.get("MsgErro")))

        if len(messages) > 0:
            return {
                "success": False,
                "price": 12,
                "error_message": "\n".join(messages),
            }
        else:
            return {
                "success": True,
                "price": total,
                "warning_message": "Prazo de entrega: {} dias".format(
                    data.get("PrazoEntrega")
                ),
            }

    def _get_correios_tracking_ref(self, picking):
        cnpj_empresa = re.sub(
            "[^0-9]", "", picking.company_id.cnpj_cpf or ""
        )

        client = self.get_correio_sigep()

        if self.ambiente == "1":
            import random

            etiqueta = [
                "PM{} BR".format(random.randrange(10000000, 99999999))
            ]
        else:
            etiqueta = client.solicita_etiquetas(
                "C", cnpj_empresa, self.service_id.identifier, 1
            )
        if len(etiqueta) > 0:
            digits = client.gera_digito_verificador_etiquetas(etiqueta)
            return etiqueta[0].replace(" ", str(digits[0]))
        else:
            raise UserError("Nenhuma etiqueta recebida")

    def _create_correio_postagem(self, picking, plp, item, package=False):
        tracking_ref = self._get_correios_tracking_ref(picking)

        if package:
            weight = sum(
                line.product_id.weight
                for line in picking.move_line_ids.filtered(
                    lambda x: x.result_package_id == item
                )
            )
            height = item.packaging_id.height
            width = item.packaging_id.width
            length = item.packaging_id.length
            diameter = 0
        else:
            weight = item.product_id.weight
            height = item.product_id.altura
            width = item.product_id.largura
            length = item.product_id.comprimento
            diameter = item.product_id.diametro

        self.env["delivery.correios.postagem.objeto"].create(
            {
                "name": tracking_ref,
                "stock_move_id": item.id if not package else False,
                "stock_package_id": item.id if package else False,
                "plp_id": plp.id,
                "delivery_id": self.id,
                "partner_id": picking.partner_id.id,
                "weight": weight,
                "height": height,
                "width": width,
                "length": length,
                "diameter": diameter,
            }
        )

        return tracking_ref

    def correios_rate_shipment(self, order):
        return self._get_normal_shipping_rate(order)

    def correios_send_shipping(self, pickings):
        """ Send the package to the service provider

        :param pickings: A recordset of pickings
        :return list: A list of dictionaries (one per picking) containing of
                    the form::
                         { 'exact_price': price,
                           'tracking_number': number }
        """

        plp = self.env["delivery.correios.postagem.plp"].search(
            [("state", "=", "draft")], limit=1
        )
        if not len(plp):
            name = "%s - %s" % (
                self.name,
                datetime.now().strftime("%d-%m-%Y"),
            )
            plp = self.env["delivery.correios.postagem.plp"].create(
                {
                    "name": name,
                    "state": "draft",
                    "delivery_id": self.id,
                    "total_value": 0,
                }
            )
        res = []
        for picking in pickings:

            tags = []
            preco_soma = 0

            package_ids = picking.move_line_ids.mapped("result_package_id")

            lines_without_package = picking.move_line_ids.filtered(
                lambda x: not x.result_package_id
            )

            origem = re.sub("[^0-9]", "", picking.company_id.zip or "")
            destino = re.sub("[^0-9]", "", picking.partner_id.zip or "")

            messages = []

            for pack in package_ids:
                lines = picking.move_line_ids.filtered(
                    lambda x: x.result_package_id == pack
                )

                param = self._get_price_params_per_packaging(
                    origem,
                    destino,
                    pack.packaging_id,
                    sum(
                        line.product_id.weight * line.product_uom_qty
                        for line in lines
                    ),
                )

                data = self.get_correio_sigep().calcular_preco_prazo(
                    **param[0][1]
                )

                if data.get("Erro") == "0":
                    preco_soma += float(data.get("Valor").replace(",", "."))
                else:
                    messages.append(
                        "{0} - {1}".format(param[0][0], data.get("MsgErro"))
                    )

                tracking_ref = self._create_correio_postagem(
                    picking, plp, pack, True
                )

                tags.append(tracking_ref)

            for line in lines_without_package:

                param = self._get_price_params_per_line(origem, destino, line)

                data = self.get_correio_sigep().calcular_preco_prazo(
                    **param[0][1]
                )

                if data.get("Erro") == "0":
                    preco_soma += float(data.get("Valor").replace(",", "."))
                else:
                    messages.append(
                        "{0} - {1}".format(
                            param.keys()[0], data.get("MsgErro")
                        )
                    )

                tracking_ref = self._create_correio_postagem(
                    picking, plp, line
                )

                tags.append(tracking_ref)

            if messages:
                msg = "Erro ao validar {}\r\n".format(picking.name)
                msg += "\r\n".join(messages)
                raise UserError(msg)

            tags = ";".join(tags)
            picking.carrier_tracking_ref = tags
            res.append({"exact_price": preco_soma, "tracking_number": tags})
            plp.total_value = preco_soma
        return res

    def get_correio_eventos(self, picking):

        # TODO Find out why this always return 'Usuário ou senha inválidos'

        client = zeep.Client(
            "http://webservice.correios.com.br/service/rastro/Rastro.wsdl"
        )
        params = {
            "usuario": self.correio_login,
            "senha": self.correio_password,
            "tipo": "L",
            "resultado": "U",
            "lingua": 101,
            "objetos": picking.carrier_tracking_ref.replace(";", "")
        }
        return client.service.buscaEventos(**params)

    def correios_get_tracking_link(self, pickings):
        """ Ask the tracking link to the service provider

        :param pickings: A recordset of pickings
        :return list: A list of string URLs, containing the tracking links
         for every picking
        """

        for picking in pickings:

            objects = self.get_correio_eventos(picking)

            for obj in objects.objeto:

                if len(obj.erro) > 0:
                    continue

                postagem = self.env[
                    'delivery.correios.postagem.objeto'
                ].search([('name', '=', obj.numero)])

                correio_evento = {
                    "etiqueta": postagem.name,
                    "postagem_id": postagem.id,
                }

                if hasattr(obj, "evento"):
                    for event in obj.evento:
                        correio_evento.update({
                            "status": event.status,
                            "data": datetime.strptime(
                                str(event.data), "%d/%m/%Y"
                            ),
                            "local": (
                                event.local
                                + " - "
                                + str(event.codigo)
                                + ", "
                                + event.cidade
                                + "/"
                                + event.uf
                            ),
                            "descricao": event.descricao,
                            "detalhe": event.detalhe,
                        })
                    self.env["delivery.correios.postagem.eventos"].create(
                        correio_evento
                    )

        # TODO Return some link after fix get_correios_eventos

        return False

    def correios_cancel_shipment(self, picking):
        """ Cancel a shipment
        """
        refs = picking.carrier_tracking_ref.split(";")
        objects = self.env["delivery.correios.postagem.objeto"].search(
            [("name", "in", refs)]
        )
        client = self.get_correio_sigep()
        for obj in objects:
            client.bloquear_objeto(obj.name, obj.plp_id.id)
        picking.write({"carrier_tracking_ref": "", "carrier_price": 0.0})
