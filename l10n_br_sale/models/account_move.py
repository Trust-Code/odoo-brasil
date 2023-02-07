from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    modalidade_frete = fields.Selection(
        [('0', '0 - Contratação do Frete por conta do Remetente (CIF)'),
         ('1', '1 - Contratação do Frete por conta do Destinatário (FOB)'),
         ('2', '2 - Contratação do Frete por conta de Terceiros'),
         ('3', '3 - Transporte Próprio por conta do Remetente'),
         ('4', '4 - Transporte Próprio por conta do Destinatário'),
         ('9', '9 - Sem Ocorrência de Transporte')],
        string=u'Modalidade do frete', default="9")
    quantidade_volumes = fields.Integer('Qtde. Volumes')
    especie = fields.Char(string="Espécie", size=60)
    peso_liquido = fields.Float(string="Peso Líquido")
    peso_bruto = fields.Float(string="Peso Bruto")
