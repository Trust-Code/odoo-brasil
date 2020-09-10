import zeep
import requests
from xml.etree import ElementTree
from zeep import helpers
from zeep.exceptions import Fault

from odoo import models, fields
from odoo.exceptions import UserError
from odoo.addons.delivery_correios.helpers.helpers import (
    URLS,
    validar,
    trim,
    gera_digito_verificador,
)


class CorreiosSigep(models.TransientModel):
    _name = "correios.sigep"

    url = fields.Char(string="Url", compute="_compute_url")
    login = fields.Char(string="login")
    password = fields.Char(string="Password")
    environment = fields.Selection([("1", "Test"), ("2", "Production")])

    def _compute_url(self):
        for item in self:
            item.url = URLS[int(item.environment)]

    def _get_client(self):
        return zeep.Client(self.url)

    def calcular_preco_prazo(
        self,
        numero_servico,
        cep_origem,
        cep_destino,
        peso,
        formato,
        comprimento,
        altura,
        largura,
        diametro,
        mao_propria,
        valor_declarado,
        aviso_recebimento,
        cod_administrativo=False,
        senha=False,
    ):

        params = {
            "nCdEmpresa": cod_administrativo or "",
            "sDsSenha": senha or "",
            "nCdServico": numero_servico,
            "sCepOrigem": cep_origem,
            "sCepDestino": cep_destino,
            "nVlPeso": peso,
            "nCdFormato": formato,
            "nVlComprimento": comprimento,
            "nVlAltura": altura,
            "nVlLargura": largura,
            "nVlDiametro": diametro,
            "sCdMaoPropria": "S" if mao_propria else "N",
            "nVlValorDeclarado": valor_declarado,
            "sCdAvisoRecebimento": "S" if aviso_recebimento else "N",
        }

        url = "http://ws.correios.com.br/calculador/CalcPrecoPrazo.aspx?\
sCepOrigem={sCepOrigem}&sCepDestino={sCepDestino}&nVlPeso={nVlPeso}\
&nCdFormato={nCdFormato}&nVlComprimento={nVlComprimento}\
&nVlAltura={nVlAltura}&nVlLargura={nVlLargura}&sCdMaoPropria={sCdMaoPropria}\
&nVlValorDeclarado={nVlValorDeclarado}&sCdAvisoRecebimento={sCdAvisoRecebimento}\
&nCdServico={nCdServico}&nVlDiametro={nVlDiametro}&StrRetorno=xml&\
nIndicaCalculo=3&nCdEmpresa={nCdEmpresa}&sDsSenha={sDsSenha}".format(
            **params
        )

        response = requests.get(url)

        tree = ElementTree.fromstring(response.content)

        data = tree.getchildren()[0]

        res = {}

        for item in data.iter():
            res.update({item.tag: item.text})

        return res

    def fecha_plp(self, xml, id_plp, numero_cartao, lista_etiquetas):
        params = {
            "xml": xml,
            "idPlpCliente": id_plp,
            "cartaoPostagem": numero_cartao,
            "listaEtiquetas": lista_etiquetas,
            "usuario": self.login,
            "senha": self.password,
        }
        return self._get_client().service.fechaPlpVariosServicos(**params)

    def bloquear_objeto(self, numero_etiqueta, id_plp):
        params = {
            "numeroEtiqueta": numero_etiqueta,
            "idPlp": id_plp,
            "tipoBloqueio": "FRAUDE_BLOQUEIO",
            "acao": "DEVOLVIDO_AO_REMETENTE",
            "usuario": self.login,
            "senha": self.password,
        }
        return self._get_client().service.bloquearObjeto(**params)

    def busca_cliente(self, id_contrato, id_cartao_postagem):
        try:
            params = {
                "idContrato": id_contrato,
                "idCartaoPostagem": id_cartao_postagem,
                "usuario": self.login,
                "senha": self.password,
            }

            validar("idContrato", params["idContrato"])
            validar("idCartaoPostagem", params["idCartaoPostagem"])

            return helpers.serialize_object(
                self._get_client().service.buscaCliente(**params), target_cls=dict
            )
        except Fault as e:
            raise UserError(str(e))

    def solicita_etiquetas(
        self, tipo_destinatario, cnpj, id_servico, qtd_etiquetas
    ):
        """Retorna uma dada quantidade de etiquetas sem o digito verificador.

        Arguments:
            tipo_destinatario {str} -- Identificação com a letra “C”,
                de cliente
            cnpj {str} -- CNPJ da empresa.
            id_servico {int} -- Id do serviço, porderá ser obtido no método
                buscaCliente().
            qtd_etiquetas {int} -- Quantidade de etiquetas a serem solicitadas.

        Returns:
            list -- Lista de etiquetas
        """

        params = {
            "tipoDestinatario": tipo_destinatario,
            "identificador": trim(cnpj),
            "idServico": id_servico,
            "qtdEtiquetas": qtd_etiquetas,
            "usuario": self.login,
            "senha": self.password,
        }

        validar("tipoDestinatario", params["tipoDestinatario"])
        validar("cnpj", params["identificador"])

        etiquetas_str = self._get_client().service.solicitaEtiquetas(**params)
        etiquetas_lista = etiquetas_str.split(",")

        return etiquetas_lista

    def gera_digito_verificador_etiquetas(self, etiquetas, offline=True):

        params = {
            "etiquetas": etiquetas,
            "usuario": self.login,
            "senha": self.password,
        }

        for etiqueta in etiquetas:
            validar("etiqueta", etiqueta)

        if offline:
            digitos = gera_digito_verificador(params["etiquetas"])
        else:
            digitos = self._get_client().service.geraDigitoVerificadorEtiquetas(
                **params
            )

        return digitos
