# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CartaCorrecaoEletronicaEvento(models.Model):
    _name = 'carta.correcao.eletronica.evento'

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
