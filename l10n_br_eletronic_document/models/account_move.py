from datetime import datetime
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_br_edoc_policy = fields.Selection(
        [('directly', 'Emitir agora'),
         ('after_payment', 'Emitir após pagamento'),
         ('manually', 'Manualmente')], string="Nota Eletrônica", default='directly')

    def _prepare_eletronic_doc_vals(self):
        return {
            'name': self.name,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'move_id': self.id,
            'schedule_user_id': self.env.user.id,
            'state': 'draft',
            'tipo_operacao': 'saida',
            'data_agendada': self.invoice_date,
            'finalidade_emissao': '1',
            'partner_id': self.partner_id.id,
            'payment_term_id': self.invoice_payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
            'valor_final': self.amount_total,
        }

    def _prepare_eletronic_line_vals(self, lines):
        result = []
        for line in lines:
            result += [(0, 0, {
                'name': line.name,
                'product_id': line.product_id.id,
                #'tipo_produto': line.product_type,
                #'cfop': line.cfop_id.code,
                'uom_id': line.product_uom_id.id,
                'quantidade': line.quantity,
                'preco_unitario': line.price_unit,
                #'valor_bruto': line.valor_bruto,
                #'desconto': line.valor_desconto,
                'valor_liquido': line.price_subtotal,
                #'origem': line.icms_origem,
                #'tributos_estimados': line.tributos_estimados,
                #'ncm': line.fiscal_classification_id.code,
                #'pedido_compra': line.pedido_compra,
                #'item_pedido_compra': line.item_pedido_compra,
            })]
        return result


    def action_create_eletronic_document(self):
        for move in self:
            vals = move._prepare_eletronic_doc_vals()
            services = move.invoice_line_ids.filtered(lambda  x: x.product_id.type == 'service')
            if services:
                vals['model'] = 'nfse'
                vals['document_line_ids'] = self._prepare_eletronic_line_vals(services)
                self.env['eletronic.document'].create(vals)
            products = move.invoice_line_ids.filtered(lambda  x: x.product_id.type != 'service')
            if products:
                vals['model'] = 'nfe'
                vals['document_line_ids'] = self._prepare_eletronic_line_vals(products)
                self.env['eletronic.document'].create(vals)

    def action_post(self):
        res = super(AccountMove, self).action_post()
        moves = self.filtered(lambda x: x.l10n_br_edoc_policy == 'directly')
        moves.action_create_eletronic_document()
        return res
