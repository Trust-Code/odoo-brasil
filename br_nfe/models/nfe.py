# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ImportDeclaration(models.Model):
    _inherit = 'br_account.import.declaration'

    invoice_eletronic_line_id = fields.Many2one(
        'invoice.eletronic', u'Linha de Documento Eletrônico',
        ondelete='cascade', select=True)


class NfeReboque(models.Model):
    _name = 'nfe.reboque'

    invoice_eletronic_id = fields.Many2one('invoice.eletronic', string="NFe")
    placa_veiculo = fields.Char(string="Placa", size=7)
    uf_veiculo = fields.Char(string=u"UF Veículo", size=2)
    rntc = fields.Char(string="RNTC", size=20,
                       help="Registro Nacional de Transportador de Carga")
    vagao = fields.Char(string=u"Vagão", size=20)
    balsa = fields.Char(string="Balsa", size=20)


class NfeVolume(models.Model):
    _name = 'nfe.volume'

    invoice_eletronic_id = fields.Many2one('invoice.eletronic', string="NFe")
    quantidade_volumes = fields.Integer(string="Qtde. Volumes")
    especie = fields.Char(string=u"Espécie", size=60)
    marca = fields.Char(string="Marca", size=60)
    numeracao = fields.Char(string=u"Numeração", size=60)
    peso_liquido = fields.Integer(string=u"Peso Líquido")
    peso_bruto = fields.Integer(string="Peso Bruto")


class NFeCobrancaDuplicata(models.Model):
    _name = 'nfe.duplicata'
    _order = 'data_vencimento'

    invoice_eletronic_id = fields.Many2one('invoice.eletronic', string="NFe")
    currency_id = fields.Many2one(
        'res.currency', related='invoice_eletronic_id.currency_id',
        string="EDoc Currency", readonly=True)
    numero_duplicata = fields.Char(string=u"Número Duplicata", size=60)
    data_vencimento = fields.Date(string="Data Vencimento")
    valor = fields.Monetary(string="Valor Duplicata")
