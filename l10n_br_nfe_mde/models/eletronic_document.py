from odoo import fields, models

STATE = {'edit': [('readonly', False)]}


class EletronicDocument(models.Model):
    _inherit = 'eletronic.document'

    nfe_mde_id = fields.Many2one(
        'nfe.mde', string=u"Manifesto Eletrônico",
        readonly=True)


# class InvoiceEletronicEvent(models.Model):
#     _inherit = 'invoice.eletronic.event'

#     nfe_mde_id = fields.Many2one(
#         'nfe.mde', string=u"Manifesto Eletrônico",
#         readonly=True, states=STATE)
