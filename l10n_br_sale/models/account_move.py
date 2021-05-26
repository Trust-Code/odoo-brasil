from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    carrier_partner_id = fields.Many2one('res.partner', string='Transportadora')
    modalidade_frete = fields.Selection(
        [('0', '0 - Contratação do Frete por conta do Remetente (CIF)'),
         ('1', '1 - Contratação do Frete por conta do Destinatário (FOB)'),
         ('2', '2 - Contratação do Frete por conta de Terceiros'),
         ('3', '3 - Transporte Próprio por conta do Remetente'),
         ('4', '4 - Transporte Próprio por conta do Destinatário'),
         ('9', '9 - Sem Ocorrência de Transporte')],
        string=u'Modalidade do frete', default="9")
    num_volumes = fields.Integer('Quant. total de volumes')
    quant_peso = fields.Float('Peso')
    # peso_uom = fields.Many2one('uom.uom')

    nfe_number = fields.Integer(
        string=u"Número NFe", compute="_compute_nfe_number")

    def _compute_nfe_number(self):
        for item in self:
            docs = self.env['eletronic.document'].search(
                [('move_id', '=', item.id)])
            if docs:
                item.nfe_number = docs[0].numero
            else:
                item.nfe_number = 0