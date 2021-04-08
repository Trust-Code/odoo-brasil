from odoo import models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"
    
    def compute(self, value, date_ref=False, currency=None):
        if self.env.context.get('eletronic_doc_id'):
            edoc = self.env.context.get('eletronic_doc_id')
            if edoc.duplicata_ids:
                result = [(x.data_vencimento, x.valor) for x in edoc.duplicata_ids]
                return result
        return super(AccountPaymentTerm, self).compute(
            value, date_ref=date_ref, currency=currency)