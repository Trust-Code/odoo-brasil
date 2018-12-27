# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com> Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _compute_invoices(self):
        for picking in self:
            total = self.env['account.invoice'].search_count(
                [('picking_origin_id', '=', picking.id)])
            picking.invoice_count = total

    invoice_count = fields.Integer(
        string="Invoices", compute='_compute_invoices')
    enable_invoicing = fields.Boolean(
        related='picking_type_id.enable_invoicing', readonly=True)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Posição Fiscal")

    def _prepare_inv_line_vals(self, move_line_id):
        linevals = {
            'product_id': move_line_id.product_id.id,
            'quantity': move_line_id.qty_done,
            'price_unit': move_line_id.product_id.lst_price,
            'invoice_id': self.env['account.invoice'].new({
                'fiscal_position_id': self.fiscal_position_id.id,
                'type': 'out_invoice',
                'partner_id': self.partner_id.id,
            })
        }
        line = self.env['account.invoice.line'].new(linevals)
        line._br_account_onchange_product_id()
        line._onchange_product_id()
        linevals = line._convert_to_write(
            {name: line[name] for name in line._cache})
        vals = {k: v for k, v in linevals.items() if v}
        vals.update({
            'quantity': move_line_id.qty_done,
            'price_unit': move_line_id.product_id.lst_price,
        })
        return vals

    def _prepare_invoice_values(self):
        inv_line_vals = []
        for picking in self:
            for line in picking.move_line_ids:
                vals = picking._prepare_inv_line_vals(line)
                inv_line_vals += [(0, 0, vals)]

        picking_id = self[0]
        vals = {
            'type': 'out_invoice',
            'partner_id': picking_id.partner_id.id,
            'payment_term_id':
            picking_id.partner_id.property_payment_term_id.id,
            'fiscal_position_id':
            picking_id.partner_id.property_account_position_id.id,
            'invoice_line_ids': inv_line_vals,
            'picking_origin_id': picking_id.id,
        }
        if self.fiscal_position_id:
            fpos = self.fiscal_position_id
            vals['fiscal_position_id'] = fpos.id
            vals['product_document_id'] = fpos.product_document_id.id
            vals['product_serie_id'] = fpos.product_serie_id.id
            vals['service_document_id'] = fpos.service_document_id.id
            vals['service_serie_id'] = fpos.service_serie_id.id
        if self.fiscal_position_id.fiscal_observation_ids:
            vals['fiscal_observation_ids'] = [
                (6, None, self.fiscal_position_id.fiscal_observation_ids.ids)]
        return vals

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        pickings_to_invoice = self.filtered(
            lambda x: x.picking_type_id.enable_invoicing)
        if pickings_to_invoice:
            pickings_to_invoice.action_invoice_picking()
        return res

    @api.multi
    def action_invoice_picking(self):
        partner_ids = self.mapped('partner_id')
        if not partner_ids:
            raise UserError('No partner to invoice, please choose one!')
        invoice_ids = self.env['account.invoice']
        for partner_id in partner_ids:
            picking_ids = self.filtered(lambda x: x.partner_id == partner_id)

            inv_vals = picking_ids._prepare_invoice_values()
            invoice_ids |= self.env['account.invoice'].create(inv_vals)
        invoice_ids.action_invoice_open()
        return invoice_ids


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    enable_invoicing = fields.Boolean(string="Enable Invoicing", default=False)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Posição Fiscal")
