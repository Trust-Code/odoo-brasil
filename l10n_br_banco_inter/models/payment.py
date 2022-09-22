from odoo import fields, models
from odoo.exceptions import UserError


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("boleto-inter", "Boleto Banco Inter")], ondelete = { 'boleto-inter' : 'set default' })


class PaymentTransaction(models.Model):
    _name = 'payment.transaction'
    _inherit = ['payment.transaction', 'banco.inter.mixin']

    boleto_pdf = fields.Binary(string="Boleto PDF")

    def action_get_pdf_inter(self):
        attachment_ids = []
        for transaction in self:
            if transaction.acquirer_id.provider != 'boleto-inter':
                continue

            journal_id = self.acquirer_id.journal_id
            boleto_data = self.get_boleto_inter_pdf(journal_id, transaction.acquirer_reference)

            filename = "%s - Boleto - %s.%s" % (transaction.partner_id.name_get()[0][1], transaction.reference, "pdf")
            boleto_id = self.env['ir.attachment'].create(dict(
                name=filename,
                datas= boleto_data,
                mimetype='application/pdf',
                res_model='account.move',
                res_id=transaction.invoice_ids and transaction.invoice_ids[0].id or False
            ))
            attachment_ids.append(boleto_id.id)
        return attachment_ids

    def action_verify_transaction(self):
        if self.acquirer_id.provider != 'boleto-inter':
            return super(PaymentTransaction, self).action_verify_transaction()
        if not self.acquirer_reference:
            raise UserError('Esta transação não foi enviada a nenhum gateway de pagamento')

        journal_id = self.acquirer_id.journal_id
        situacao = self.get_boleto_inter_status(journal_id, self.acquirer_reference)

        if situacao == "PAGO":
            self._set_transaction_done()
            self._post_process_after_done()
        elif situacao == "BAIXADO":
            self._set_transaction_cancel()

    def action_cancel_transaction(self):
        if self.acquirer_id.provider != 'boleto-inter':
            return super(PaymentTransaction, self).action_cancel_transaction()

        self._set_transaction_cancel()
        journal_id = self.acquirer_id.journal_id
        self.cancel_boleto_inter(journal_id, self.acquirer_reference)

    def _find_attachment_ids_email(self):
        atts = super()._find_attachment_ids_email()
        atts += self.action_get_pdf_inter()
        return atts

