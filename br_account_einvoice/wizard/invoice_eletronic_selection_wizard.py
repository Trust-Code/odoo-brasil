from odoo import models, fields


class InvoiceEletronicSelectionWizard(models.TransientModel):
    _name = 'invoice.eletronic.selection.wizard'

    def _default_invoice_id(self):
        return self.env.context.get('active_id')

    invoice_id = fields.Many2one(
        'account.invoice', default=_default_invoice_id)

    einvoice_id = fields.Many2one(
        'invoice.eletronic', string="E-Invoice",
        domain="[('invoice_id', '=', invoice_id)]",
        required=True)

    def action_confirm(self):
        if self.einvoice_id:
            return self.invoice_id._action_preview_danfe(self.einvoice_id)
