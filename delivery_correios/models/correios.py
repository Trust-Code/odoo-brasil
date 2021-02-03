# © 2020 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import re
import logging
import os
import requests
import base64
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from lxml import etree
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError

from zeep.exceptions import Fault

_logger = logging.getLogger(__name__)


class CorreiosServicos(models.Model):
    _name = "delivery.correios.service"

    code = fields.Char(string="Código", size=20)
    identifier = fields.Char(string="Identificador", size=20)
    name = fields.Char(string="Descrição", size=70, required=True)
    delivery_id = fields.Many2one("delivery.carrier", string="Método entrega")
    chancela = fields.Binary(string="Chancela")
    ano_assinatura = fields.Char(string="Ano Assinatura")


class CorreiosPostagemPlp(models.Model):
    _name = "delivery.correios.postagem.plp"

    name = fields.Char(string="Descrição", size=20, required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        default=lambda self: self.env.user.company_id.id,
    )
    state = fields.Selection(
        [("draft", "Rascunho"), ("done", "Enviado")],
        string="Status",
        default="draft",
    )
    delivery_id = fields.Many2one("delivery.carrier", string="Método entrega")
    total_value = fields.Float(string="Valor Total")
    sent_date = fields.Date(string="Data Envio")
    id_plp_correios = fields.Char(string="Id Plp Correios", size=30)
    postagem_ids = fields.One2many(
        "delivery.correios.postagem.objeto", "plp_id", string="Postagens"
    )

    def unlink(self):
        for item in self:
            if item.state == "done":
                raise UserError("Não é possível excluir uma PLP já enviada")
        return super(CorreiosPostagemPlp, self).unlink()

    def plp_barcode_url(self):
        web_base_url = self.env["ir.config_parameter"].search(
            [("key", "=", "web.base.url")], limit=1
        )

        url = "{}/report/barcode/?type={}&value={}&width={}&height={}".format(
            web_base_url.value, 'Code128', self.id_plp_correios, 350, 40
        )

        response = requests.get(url)

        return base64.b64encode(response.content).decode("utf-8")


    @api.model
    def _get_post_services(self):
        services = {}
        for item in self.postagem_ids:
            serv = item.delivery_id.service_id

            if serv.id not in services:
                services[serv.id] = {}
                services[serv.id]["name"] = serv.name
                services[serv.id]["code"] = serv.code
                services[serv.id]["quantity"] = 0

            services[serv.id]["quantity"] += 1
        return services

    def get_plp_xml(self, **dados):
        path = os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]
        env = Environment(
            loader=FileSystemLoader(os.path.join("/", *path, "templates")),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
        )
        xml = env.get_template("fecha_plp_varios_servicos.xml").render(dados)
        parser = etree.XMLParser(
            remove_blank_text=True, encoding="ISO-8859-1"
        )
        elem = etree.XML(xml, parser=parser)
        xml = etree.tostring(elem)
        return xml

    def action_generate_voucher(self):
        dados = {
            "cartaoPostagem": self.delivery_id.cartao_postagem,
            "numero_contrato": self.delivery_id.num_contrato,
            "numero_diretoria": "36",
            "codigo_administrativo": self.delivery_id.cod_administrativo,
            "nome_remetente": self.company_id.legal_name,
            "logradouro_remetente": self.company_id.street,
            "numero_remetente": self.company_id.number,
            "complemento_remetente": self.company_id.street2 or "",
            "bairro_remetente": self.company_id.district,
            "cep_remetente": re.sub("[^0-9]", "", self.company_id.zip or ""),
            "cidade_remetente": self.company_id.city_id.name,
            "uf_remetente": self.company_id.state_id.code,
            "telefone_remetente": re.sub(
                "[^0-9]", "", self.company_id.phone or ""
            ),
            "email_remetente": self.company_id.email,
        }
        postagens = []
        etiquetas = []
        for item in self.postagem_ids:
            etiqueta = item.name[:10] + item.name[11:]
            etiquetas.append(etiqueta)

            postagens.append(
                {
                    "numero_etiqueta": item.name,
                    "codigo_servico_postagem":
                    item.delivery_id.service_id.code.strip(),
                    "peso": "%d" % (item.weight * 1000),
                    "nome_destinatario": item.partner_id.legal_name
                    or item.partner_id.name,
                    "telefone_destinatario": re.sub(
                        "[^0-9]", "", item.partner_id.phone or ""
                    ),
                    "celular_destinatario": re.sub(
                        "[^0-9]", "", item.partner_id.mobile or ""
                    ),
                    "email_destinatario": item.partner_id.email,
                    "logradouro_destinatario": item.partner_id.street,
                    "complemento_destinatario": item.partner_id.street2 or "",
                    "numero_end_destinatario": item.partner_id.number,
                    "bairro_destinatario": item.partner_id.district,
                    "cidade_destinatario": item.partner_id.city_id.name,
                    "uf_destinatario": item.partner_id.state_id.code,
                    "cep_destinatario": re.sub(
                        "[^0-9]", "", item.partner_id.zip or ""
                    ),
                    "descricao_objeto": item.stock_move_id.product_id.name,
                    "valor_a_cobrar": "0",
                    "valor_declarado": "0",
                    "tipo_objeto": "2",
                    "altura": "%d" % item.height,
                    "largura": "%d" % item.width,
                    "comprimento": "%d" % item.length,
                    "diametro": "%d" % item.diameter,
                    "servicos_adicionais": ["019", "001"],
                }
            )
        dados["objetos"] = postagens

        xml_to_send = self.get_plp_xml(**dados)

        try:
            idPlpCorreios = self.delivery_id.get_correio_sigep().fecha_plp(
                xml_to_send,
                self.id,
                self.delivery_id.cartao_postagem,
                etiquetas,
            )
        except Fault as e:
            raise UserError(e.message)

        self.write(
            {
                "sent_date": datetime.now(),
                "state": "done",
                "id_plp_correios": idPlpCorreios,
            }
        )

    def get_company_logo(self):

        logo = self.with_context({"bin_size": False}).company_id.logo.decode(
            "utf-8"
        )

        return (
            '<img class="header-logo" style="max-height: 95px; width: 95px;"\
src="data:image/png;base64,'
            + logo
            + '"/>'
        )

    def get_chancela(self):

        chancela = self.with_context(
            {"bin_size": False}
        ).delivery_id.service_id.chancela.decode("utf-8")

        return (
            '<img class="header-chancela" style="height: 75px; width: 75px;"\
src="data:image/png;base64,'
            + chancela
            + '"/>'
        )


class CorreiosPostagemObjeto(models.Model):
    _name = "delivery.correios.postagem.objeto"

    name = fields.Char(string="Descrição", size=20, required=True)
    delivery_id = fields.Many2one("delivery.carrier", string="Método entrega")
    stock_move_id = fields.Many2one("stock.move", string="Item Entrega")
    stock_package_id = fields.Many2one(
        "stock.quant.package", string="Pacote de Entrega"
    )
    plp_id = fields.Many2one("delivery.correios.postagem.plp", "PLP")
    evento_ids = fields.One2many(
        "delivery.correios.postagem.eventos", "postagem_id", "Eventos"
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner"
    )
    weight = fields.Float(string="Weight")
    height = fields.Integer(string="Height")
    width = fields.Integer(string="Width")
    length = fields.Integer(string="Length")
    diameter = fields.Integer(string="Diameter")

    def _get_barcode_image(self, barcode_type, code, width, height):
        web_base_url = self.env["ir.config_parameter"].search(
            [("key", "=", "web.base.url")], limit=1
        )

        url = "{}/report/barcode/?type={}&value={}&width={}&height={}".format(
            web_base_url.value, barcode_type, code, width, height
        )
        response = requests.get(url)

        image = base64.b64encode(response.content)
        return image.decode("utf-8")

    def tracking_qrcode(self):
        origem = self.plp_id.company_id
        destino = self.partner_id

        dados = {}

        dados["destino_cep"] = re.sub("[^0-9]", "", destino.zip or "")
        dados["destino_compl"] = re.sub(
            r"\D", "", destino.number or ""
        ).zfill(5)
        dados["origem_cep"] = re.sub("[^0-9]", "", origem.zip or "")
        dados["origem_compl"] = re.sub(
            r"\D", "", origem.number or ""
        ).zfill(5)
        validador_cep_dest = sum(
            [int(n) for n in re.sub(r"\D", "", destino.zip) or ""]
        )
        next_10 = validador_cep_dest
        while next_10 % 10 != 0:
            next_10 += 1
        dados["validador_cep_dest"] = next_10 - validador_cep_dest

        dados["idv"] = "51"

        dados["etiqueta"] = self.name

        transportadora = self.plp_id.delivery_id
        servicos_adicionais = ""
        servicos_adicionais += (
            "01" if transportadora.aviso_recebimento == "S" else "00"
        )
        servicos_adicionais += (
            "02" if transportadora.mao_propria == "S" else "00"
        )
        servicos_adicionais += (
            "19" if transportadora.valor_declarado else "00"
        )
        dados["servicos_adicionais"] = servicos_adicionais.ljust(12, "0")

        dados["cartao_postagem"] = transportadora.cartao_postagem.zfill(10)
        dados["codigo_servico"] = transportadora.service_id.code
        dados["agrupamento"] = "00"
        dados["num_logradouro"] = destino.number.zfill(5) or "0" * 5
        dados["compl_logradouro"] = "{:.20}".format(
            str(destino.street2 or "")
        ).zfill(20)
        dados["valor_declarado"] = (
            #str(self.product_id * self.product_qty)
            str(" ")
            .replace(".", "")
            .replace(",", "")
            .zfill(5)
            if transportadora.valor_declarado
            else "00000"
        )
        if destino.phone:
            telefone = (
                re.sub(r"\D", "", destino.phone).replace(" ", "").zfill(12)
            )
        elif destino.mobile:
            telefone = (
                re.sub(r"\D", "", destino.mobile).replace(" ", "").zfill(12)
            )
        else:
            telefone = "0" * 12
        dados["telefone"] = telefone
        dados["latitude"] = "-00.000000"
        dados["longitude"] = "-00.000000"
        dados["pipe"] = "|"
        dados["reserva"] = " " * 30
        code = "{destino_cep}{destino_compl}{origem_cep}{origem_compl}\
{validador_cep_dest}{idv}{etiqueta}{servicos_adicionais}{cartao_postagem}\
{codigo_servico}{agrupamento}{num_logradouro}{compl_logradouro}\
{valor_declarado}{telefone}{latitude}{longitude}{pipe}{reserva}".format(
            **dados
        )

        return self._get_barcode_image("QR", code, 95, 95)

    def get_nfe_number(self):
        return ""

    def tracking_barcode(self):
        return self._get_barcode_image("Code128", self.name, 300, 70)

    def zip_dest_barcode(self):
        cep = re.sub("[^0-9]", "", self.partner_id.zip or "")
        return self._get_barcode_image("Code128", cep, 200, 50)


class CorreiosEventosObjeto(models.Model):
    _name = "delivery.correios.postagem.eventos"

    etiqueta = fields.Char(string="Etiqueta")
    postagem_id = fields.Many2one(
        "delivery.correios.postagem.objeto", "Postagem"
    )
    status = fields.Char(string="Status")
    data = fields.Date(string="Data")
    local = fields.Char(string="Local")
    descricao = fields.Char(string="Descrição")
    detalhe = fields.Char(string="Detalhe")
