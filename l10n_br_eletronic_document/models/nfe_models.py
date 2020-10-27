import re
import base64
import logging
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import inutilizar_nfe
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.error("Cannot import pytrustnfe", exc_info=True)


class NfeReboque(models.Model):
    _name = "nfe.reboque"
    _description = "NF-e Reboque"

    eletronic_document_id = fields.Many2one("eletronic.document", string="NFe")
    placa_veiculo = fields.Char(string="Placa", size=7)
    uf_veiculo = fields.Char(string=u"UF Veículo", size=2)
    rntc = fields.Char(
        string="RNTC", size=20, help="Registro Nacional de Transportador de Carga"
    )
    vagao = fields.Char(string=u"Vagão", size=20)
    balsa = fields.Char(string="Balsa", size=20)


class NfeVolume(models.Model):
    _name = "nfe.volume"
    _description = "NF-e Volume"

    eletronic_document_id = fields.Many2one("eletronic.document", string="NFe")
    quantidade_volumes = fields.Integer(string="Qtde. Volumes")
    especie = fields.Char(string=u"Espécie", size=60)
    marca = fields.Char(string="Marca", size=60)
    numeracao = fields.Char(string=u"Numeração", size=60)
    peso_liquido = fields.Float(string=u"Peso Líquido")
    peso_bruto = fields.Float(string="Peso Bruto")


class NFeCobrancaDuplicata(models.Model):
    _name = "nfe.duplicata"
    _description = "NF-e Duplicata"
    _order = "data_vencimento"

    eletronic_document_id = fields.Many2one("eletronic.document", string="NFe")
    currency_id = fields.Many2one(
        "res.currency",
        related="eletronic_document_id.currency_id",
        string="EDoc Currency",
        readonly=True,
        store=True,
    )
    numero_duplicata = fields.Char(string=u"Número Duplicata", size=60)
    data_vencimento = fields.Date(string="Data Vencimento")
    valor = fields.Monetary(string="Valor Duplicata")


class CartaCorrecaoEletronicaEvento(models.Model):
    _name = "carta.correcao.eletronica.evento"
    _description = "Carta de correção eletrônica"

    eletronic_document_id = fields.Many2one(
        "eletronic.document", string="Documento Eletrônico"
    )

    # Fields CCe
    id_cce = fields.Char(string="ID", size=60)
    datahora_evento = fields.Datetime(string="Data do Evento")
    tipo_evento = fields.Char(string="Código do Evento")
    sequencial_evento = fields.Integer(string="Sequencial do Evento")
    correcao = fields.Text(string="Correção", max_length=1000)
    message = fields.Char(string="Mensagem", size=300)
    protocolo = fields.Char(string="Protocolo", size=30)


STATE = {"edit": [("readonly", False)], "draft": [("readonly", False)]}


class InutilizedNfe(models.Model):
    _name = "invoice.eletronic.inutilized"
    _description = "NF-e inutilizada"

    name = fields.Char("Nome", required=True, readonly=True, states=STATE)
    numeration_start = fields.Integer(
        "Número Inicial", required=True, readonly=True, states=STATE
    )
    numeration_end = fields.Integer(
        "Número Final", required=True, readonly=True, states=STATE
    )
    justificativa = fields.Text(
        "Justificativa", required=True, readonly=True, states=STATE
    )
    state = fields.Selection(
        [
            ("draft", "Provisório"),
            ("done", "Enviado"),
            ("error", "Erro"),
            ("edit", "Editando"),
        ],
        string=u"State",
        default="edit",
        required=True,
        readonly=True,
    )
    modelo = fields.Selection(
        [("55", "55 - NFe"), ("65", "65 - NFCe"),],
        string="Modelo",
        required=True,
        readonly=True,
        states=STATE,
    )
    serie = fields.Integer(string="Série")
    code = fields.Char(string="Código", size=10)
    motive = fields.Char(string="Motivo", size=300)
    sent_xml = fields.Binary(string="Xml Envio", readonly=True)
    sent_xml_name = fields.Char(string="Xml Envio", size=30, readonly=True)
    received_xml = fields.Binary(string="Xml Recebimento", readonly=True)
    received_xml_name = fields.Char(string="Xml Recebimento", size=30, readonly=True)

    @api.model
    def create(self, vals):
        vals["state"] = "draft"
        return super(InutilizedNfe, self).create(vals)

    def validate_hook(self):
        errors = []
        docs = self.env["eletronic.document"].search(
            [
                ("numero", ">=", self.numeration_start),
                ("numero", "<=", self.numeration_end),
                ("company_id", "=", self.env.company.id),
                ("model", "=", self.modelo),
            ]
        )
        if docs:
            errors.append(
                "Não é possível invalidar essa série pois já existem"
                " documentos com essa numeração."
            )
        if self.numeration_start > self.numeration_end:
            errors.append(
                "O Começo da Numeração deve ser menor que o " "Fim da Numeração"
            )
        if self.numeration_start < 0 or self.numeration_end < 0:
            errors.append("Não é possível cancelar uma série negativa.")
        if self.numeration_end - self.numeration_start >= 10000:
            errors.append(
                "Número máximo de numeração a inutilizar ultrapassou" " o limite."
            )
        if len(self.justificativa) < 15:
            errors.append("A Justificativa deve ter no mínimo 15 caracteres")
        if len(self.justificativa) > 255:
            errors.append("A Justificativa deve ter no máximo 255 caracteres")
        if not self.env.company.l10n_br_certificate:
            errors.append("A empresa não possui um certificado de NFe " "cadastrado")
        if not self.env.company.l10n_br_cnpj_cpf:
            errors.append("Cadastre o CNPJ da empresa.")
        estado = self.env.company.state_id
        if not estado or not estado.l10n_br_ibge_code:
            errors.append("Cadastre o Estado da empresa.")
        if len(errors):
            raise UserError("\n".join(errors))
        return True

    def _prepare_obj(self, company, estado, ambiente):
        ano = str(datetime.now().year)[2:]
        cnpj = re.sub(r"\D", "", company.l10n_br_cnpj_cpf)
        ID = (
            "ID{estado:2}{ano:2}{cnpj:14}{modelo:2}"
            "{serie:03}{num_inicial:09}{num_final:09}"
        )
        ID = ID.format(
            estado=estado,
            ano=ano,
            cnpj=cnpj,
            modelo=self.modelo,
            serie=int(self.serie),
            num_inicial=self.numeration_start,
            num_final=self.numeration_end,
        )
        return {
            "id": ID,
            "ambiente": ambiente,
            "estado": estado,
            "ano": ano,
            "cnpj": cnpj,
            "modelo": self.modelo,
            "serie": self.serie,
            "numero_inicio": self.numeration_start,
            "numero_fim": self.numeration_end,
            "justificativa": self.justificativa,
        }

    def _handle_response(self, response):
        inf_inut = response["object"].getchildren()[0].infInut
        status = inf_inut.cStat
        if status == 102:
            self.write(
                {"state": "done", "code": inf_inut.cStat, "motive": inf_inut.xMotivo}
            )
            self._create_attachment("inutilizacao-envio", self, response["sent_xml"])
            self._create_attachment(
                "inutilizacao-recibo", self, response["received_xml"]
            )
        else:
            self.write(
                {
                    "state": "error",
                    "code": inf_inut.cStat,
                    "motive": inf_inut.xMotivo,
                    "sent_xml": base64.b64encode(response["sent_xml"].encode("utf-8")),
                    "sent_xml_name": "inutilizacao-envio.xml",
                    "received_xml": base64.b64encode(
                        response["received_xml"].encode("utf-8")
                    ),
                    "received_xml_name": "inutilizacao-retorno.xml",
                }
            )
            return {
                "name": "Inutilização de NFe",
                "type": "ir.actions.act_window",
                "res_model": "invoice.eletronic.inutilized",
                "res_id": self.id,
                "view_type": "form",
                "view_mode": "form",
                "target": "new",
            }

    def send_sefaz(self):
        company = self.env.company
        ambiente = 1 if company.l10n_br_tipo_ambiente == "producao" else 2
        estado = company.state_id.l10n_br_ibge_code

        obj = self._prepare_obj(company=company, estado=estado, ambiente=ambiente)

        cert = company.with_context({"bin_size": False}).l10n_br_certificate
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, company.l10n_br_cert_password)

        resposta = inutilizar_nfe(
            certificado,
            obj=obj,
            estado=estado,
            ambiente=int(ambiente),
            modelo=obj["modelo"],
        )
        return self._handle_response(response=resposta)

    def action_send_inutilization(self):
        self.validate_hook()
        retorno = self.send_sefaz()
        if retorno:
            return retorno
        return self.env.ref("br_nfe.action_invoice_eletronic_inutilized").read()[0]

    def _create_attachment(self, prefix, event, data):
        file_name = "%s-%s.xml" % (prefix, datetime.now().strftime("%Y-%m-%d-%H-%M"))
        self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": base64.b64encode(data.encode("utf-8")),
                "store_fname": file_name,
                "description": u"",
                "res_model": "invoice.eletronic.inutilized",
                "res_id": event.id,
            }
        )

