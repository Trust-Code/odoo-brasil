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
    num_volumes = fields.Integer('Quant. total de volumes', compute="_compute_volumes")
    stock_picking_ids = fields.Integer('Stock Pickings', compute="_compute_volumes")
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

    def _compute_volumes(self):
        # if item.informacao_adicional:
        #     infAdProd = item.informacao_adicional
        # else:
        #     infAdProd = ''
        if item.product_id.tracking == 'lot':
            pick = self.env['stock.picking'].search([
                ('origin', '=', self.invoice_id.origin),
                ('state', '=', 'done')])
            for line in pick.move_line_ids:
             lotes = []
        #         if line.product_id.id == item.product_id.id:
        #             for lot in line.lot_id:
        #                 lote = {
        #                     'nLote': lot.name,
        #                     'qLote': line.qty_done,
        #                     'dVal': lot.life_date.strftime('%Y-%m-%d'),
        #                     'dFab': lot.use_date.strftime('%Y-%m-%d'),
        #                 }
        #                 lotes.append(lote)
        #                 fab = fields.Datetime.from_string(lot.use_date)
        #                 vcto = fields.Datetime.from_string(lot.life_date)
        #                 infAdProd += ' Lote: %s, Fab.: %s, Vencto.: %s' \
        #                              % (lot.name, fab, vcto)
        #         prod["rastro"] = lotes
            self.write({
                'num_volumes': len(lotes),
                'stock_picking_ids': lotes.ids,
            })