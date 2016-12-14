# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CartaCorrecaoEletronicaEvento(models.Model):
    _name = 'carta.correcao.eletronica.evento'

    invoice_id = fields.Many2one('invoice.eletronic')

    # Fields CCe
    Id = fields.Char(string="Id")
    idLote = fields.Integer("Identificador de controle do Lote")
    cOrgao = fields.Char(string="Código do Orgão")
    tpAmb = fields.Selection([('2', 'Homologação'), ('1', 'Produção')],
                             string="Ambiente")
    CNPJ = fields.Char(string="CNPJ")
    CPF = fields.Char(string="CPF")
    chNFe = fields.Char(string="Chave NFe")
    dhEvento = fields.Datetime(string="Data do Evento")
    tpEvento = fields.Char(string="Código do Evento")
    nSeqEvento = fields.Integer(string="Sequencial do Evento")
    xCorrecao = fields.Text(string="Correção", max_length=1000)
