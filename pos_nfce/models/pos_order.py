# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_final_costumer(self, user_id):
        final_costumer = self.env['res.partner'].search(
            [('name', '=', 'Consumidor Final')]
        )
        if len(final_costumer) == 0:
            user = self.env['res.users'].search(
                [('id', '=', user_id['user_id'])]
            )
            final_costumer = self.env['res.partner'].create(dict(
                name='Consumidor Final',
                zip=user.company_id.partner_id.zip,
                street=user.company_id.partner_id.street,
                number=user.company_id.partner_id.number,
                district=user.company_id.partner_id.district,
                phone=user.company_id.partner_id.phone,
                country_id=user.company_id.partner_id.country_id.id,
                state_id=user.company_id.partner_id.state_id.id,
                city_id=user.company_id.partner_id.city_id.id,
                company_type='person',
                is_company=False,
                customer=True
            ))
        return final_costumer.id

    @api.multi
    def action_pos_order_invoice(self):
        Invoice = self.env['account.invoice']

        for order in self:
            # Force company for all SUPERUSER_ID action
            local_context = dict(
                self.env.context,
                force_company=order.company_id.id,
                company_id=order.company_id.id
            )
            if order.invoice_id:
                Invoice += order.invoice_id
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            invoice = Invoice.new(order._prepare_invoice())
            invoice._onchange_partner_id()
            if order.fiscal_position_id is not False:
                position_id = order.fiscal_position_id
                invoice.fiscal_position_id = position_id
                invoice.product_serie_id = \
                    position_id.product_serie_id.id
                invoice.product_document_id = \
                    position_id.product_document_id.id

                invoice.service_serie_id = \
                    position_id.service_serie_id.id
                invoice.service_document_id = \
                    position_id.service_document_id.id
                ob_ids = []
                for x in position_id.fiscal_observation_ids:
                    ob_ids.append(x.id)
                invoice.fiscal_observation_ids = [(6, False, ob_ids)]

            inv = invoice._convert_to_write({
                name: invoice[name] for name in invoice._cache
            })
            new_invoice = Invoice.with_context(local_context)
            new_invoice = new_invoice.sudo().create(inv)
            message = _("This invoice has been created "
                        "from the point of sale session: "
                        "<a href=# data-oe-model=pos.order "
                        "data-oe-id=%d>%s</a>") % \
                      (order.id, order.name)
            new_invoice.message_post(body=message)
            order.write({
                'invoice_id': new_invoice.id,
                'state': 'invoiced'
            })
            Invoice += new_invoice

            for line in order.lines:
                self.with_context(local_context)._action_create_invoice_line(
                    line,
                    new_invoice.id
                )

            new_invoice.with_context(local_context).sudo().compute_taxes()
            new_invoice._compute_amount()
            order.sudo().write({'state': 'invoiced'})

        if not Invoice:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('account.invoice_form').id,
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': Invoice and Invoice.ids[0] or False,
        }

    def _action_create_invoice_line(self, line=False, invoice_id=False):
        InvoiceLine = self.env['account.invoice.line']
        inv_name = line.product_id.name_get()[0][1]
        inv_line = {
            'invoice_id': invoice_id,
            'product_id': line.product_id.id,
            'quantity': line.qty if self.amount_total >= 0 else -line.qty,
            'account_analytic_id': self._prepare_analytic_account(line),
            'name': inv_name,
            'fiscal_classification_id':
                line.product_id.fiscal_classification_id
        }
        # Oldlin trick
        invoice_line = InvoiceLine.sudo().new(inv_line)
        invoice_line._onchange_product_id()
        invoice_line.invoice_line_tax_ids = \
            invoice_line.invoice_line_tax_ids.filtered(
                lambda t: t.company_id.id == line.order_id.company_id.id
            ).ids
        fiscal_position_id = line.order_id.fiscal_position_id
        if fiscal_position_id:
            invoice_line.invoice_line_tax_ids = fiscal_position_id.map_tax(
                invoice_line.invoice_line_tax_ids,
                line.product_id,
                line.order_id.partner_id
            )
        invoice_line.invoice_line_tax_ids = \
            invoice_line.invoice_line_tax_ids.ids
        # We convert a new id object back to a dictionary to write to
        # bridge between old and new api
        inv_line = invoice_line._convert_to_write(
            {name: invoice_line[name] for name in invoice_line._cache}
        )
        inv_line.update(
            price_unit=line.price_unit,
            discount=line.discount,
            name=inv_name
        )
        return InvoiceLine.sudo().create(inv_line)
