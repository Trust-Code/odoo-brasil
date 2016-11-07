# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class NfeReboque(models.Model):
    _name = 'nfe.reboque'

    invoice_eletronic_id = fields.Many2one('invoice.eletronic', string="NFe")
    placa_veiculo = fields.Char(string="Placa", size=7)
    uf_veiculo = fields.Char(string="UF Veículo", size=2)
    rntc = fields.Char(string="RNTC", size=20,
                       help="Registro Nacional de Transportador de Carga")
    vagao = fields.Char(string="Vagão", size=20)
    balsa = fields.Char(string="Balsa", size=20)


class NfeVolume(models.Model):
    _name = 'nfe.volume'

    invoice_eletronic_id = fields.Many2one('invoice.eletronic', string="NFe")
    quantidade_volumes = fields.Integer(string="Qtde. Volumes")
    especie = fields.Char(string="Espécie", size=60)
    marca = fields.Char(string="Marca", size=60)
    numeracao = fields.Char(string="Numeração", size=60)
    peso_liquido = fields.Integer(string="Peso Líquido")
    peso_bruto = fields.Integer(string="Peso Bruto")


class NFeCobrancaDuplicata(models.Model):
    _name = 'nfe.duplicata'

    invoice_eletronic_id = fields.Many2one('invoice.eletronic', string="NFe")
    numero_duplicata = fields.Char(string="Número Duplicata", size=60)
    data_vencimento = fields.Date(string="Data Vencimento")
    valor = fields.Char(string="Valor Duplicata")
