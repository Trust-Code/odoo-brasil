
from odoo import api, fields, models


class NfeReboque(models.Model):
    _name = 'nfe.reboque'
    _description = "NF-e Reboque"

    eletronic_document_id = fields.Many2one('eletronic.document', string="NFe")
    placa_veiculo = fields.Char(string="Placa", size=7)
    uf_veiculo = fields.Char(string=u"UF Veículo", size=2)
    rntc = fields.Char(string="RNTC", size=20,
                       help="Registro Nacional de Transportador de Carga")
    vagao = fields.Char(string=u"Vagão", size=20)
    balsa = fields.Char(string="Balsa", size=20)


class NfeVolume(models.Model):
    _name = 'nfe.volume'
    _description = "NF-e Volume"

    eletronic_document_id = fields.Many2one('eletronic.document', string="NFe")
    quantidade_volumes = fields.Integer(string="Qtde. Volumes")
    especie = fields.Char(string=u"Espécie", size=60)
    marca = fields.Char(string="Marca", size=60)
    numeracao = fields.Char(string=u"Numeração", size=60)
    peso_liquido = fields.Float(string=u"Peso Líquido")
    peso_bruto = fields.Float(string="Peso Bruto")


class NFeCobrancaDuplicata(models.Model):
    _name = 'nfe.duplicata'
    _description = "NF-e Duplicata"
    _order = 'data_vencimento'

    eletronic_document_id = fields.Many2one('eletronic.document', string="NFe")
    currency_id = fields.Many2one(
        'res.currency', related='eletronic_document_id.currency_id',
        string="EDoc Currency", readonly=True, store=True)
    numero_duplicata = fields.Char(string=u"Número Duplicata", size=60)
    data_vencimento = fields.Date(string="Data Vencimento")
    valor = fields.Monetary(string="Valor Duplicata")


class CartaCorrecaoEletronicaEvento(models.Model):
    _name = 'carta.correcao.eletronica.evento'
    _description = "Carta de correção eletrônica"

    eletronic_doc_id = fields.Many2one(
        'invoice.eletronic', string=u"Documento Eletrônico")

    # Fields CCe
    id_cce = fields.Char(string=u"ID", size=60)
    datahora_evento = fields.Datetime(string=u"Data do Evento")
    tipo_evento = fields.Char(string=u"Código do Evento")
    sequencial_evento = fields.Integer(string=u"Sequencial do Evento")
    correcao = fields.Text(string=u"Correção", max_length=1000)
    message = fields.Char(string=u"Mensagem", size=300)
    protocolo = fields.Char(string=u"Protocolo", size=30)