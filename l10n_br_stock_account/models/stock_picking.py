# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com> Trustcode
# © 2021 - Fábio Luna <fabiocluna@hotmail.com> Code 137
# License MIT (https://mit-license.org/)

from ast import literal_eval
from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _compute_invoices(self):
        for picking in self:
            total = self.env['account.move'].search_count(
                [('l10n_br_picking_origin_id', '=', picking.id)])
            picking.invoice_count = total

    invoice_count = fields.Integer(
        string="Invoices", compute='_compute_invoices')
    enable_invoicing = fields.Boolean(string="Enable Invoicing", default=False)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Posição Fiscal")

    def action_preview_danfe(self):
        invoices = self.env['account.move'].search(
            [('l10n_br_picking_origin_id', '=', self.id)])
        return invoices.action_preview_danfe()

    def _prepare_inv_line_vals(self, move_line_id):
        linevals = {
            'product_id': move_line_id.product_id.id,
            'quantity': move_line_id.qty_done,
            'price_unit': move_line_id.product_id.lst_price,
            'move_id': self.env['account.move'].new({
                'fiscal_position_id': self.fiscal_position_id.id,
                'move_type': 'out_invoice',
                'partner_id': self.partner_id.id,
            })
        }
        line = self.env['account.move.line'].new(linevals)
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
            'move_type': 'out_invoice',
            'partner_id': picking_id.partner_id.id,
            'invoice_payment_term_id':
            picking_id.partner_id.property_payment_term_id.id,
            'fiscal_position_id':
            picking_id.partner_id.property_account_position_id.id,
            'invoice_line_ids': inv_line_vals,
            'l10n_br_picking_origin_id': picking_id.id,
        }
        if self.fiscal_position_id:
            fpos = self.fiscal_position_id
            vals['fiscal_position_id'] = fpos.id
        return vals

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        self.action_invoice_picking()
        return res

    def action_invoice_picking(self):
        pickings_to_invoice = self.filtered(lambda x: x.enable_invoicing)
        partner_ids = pickings_to_invoice.mapped('partner_id')
        invoice_ids = self.env['account.move']
        for partner_id in partner_ids:
            picking_ids = pickings_to_invoice.filtered(
                lambda x: x.partner_id == partner_id
            )

            inv_vals = picking_ids._prepare_invoice_values()
            invoice_ids |= self.env['account.move'].create(inv_vals)
        return invoice_ids

    def action_stock_account_invoice(self):
        invoice_ids = self.env['account.move'].search(
            [('l10n_br_picking_origin_id', '=', self.id)])
        domain = [('id', 'in', invoice_ids.ids)]
        action = self.env['ir.actions.actions']._for_xml_id(
            'account.action_move_out_invoice_type')
        context = literal_eval(action['context'])
        context.update(self.env.context)
        context.update({'create': False})
        return dict(action, domain=domain, context=context)
