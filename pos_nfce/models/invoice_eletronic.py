# coding=utf-8
from odoo import api, fields, models


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()

        if self.model == '65' and self.partner_id.cnpj_cpf is None:
            final_costumer = self.env['res.partner'].search([('name', '=', 'Consumidor Final')])
            if final_costumer.id == self.partner_id.id:
                errors.remove(u'CNPJ/CPF do Parceiro inválido')
                errors.remove(u'Destinatário - CNPJ/CPF')
        return errors

    @api.multi
    def _prepare_eletronic_invoice_item(self, item, invoice):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_item(
            item, invoice)

        if self.model != '65':
            return res

        final_costumer = self.env['res.partner'].search(
            [('name', '=', 'Consumidor Final')]
        )
        if final_costumer.id == self.partner_id.id:
            res['dest'] = None
        return res
