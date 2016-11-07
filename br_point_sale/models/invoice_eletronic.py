# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    qrcode_hash = fields.Char(string='QR-Code hash')
    qrcode_url = fields.Char(string='QR-Code URL')

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if len(self.company_id.id_token_csc) != 6:
            errors.append("Identificador do CSC inválido")
        if not len(self.company_id.csc):
            errors.append("CSC Inválido")
        if self.partner_id.cnpj_cpf is None:
            errors.append("CNPJ/CPF do Parceiro inválido")
        return errors

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        vals = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        codigo_seguranca = {
            'cid_token': self.company_id.id_token_csc,
            'csc': self.company_id.csc,
        }
        vals['codigo_seguranca'] = codigo_seguranca
        return vals
