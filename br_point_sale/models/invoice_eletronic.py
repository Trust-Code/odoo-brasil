# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from .account_journal import metodos


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    qrcode_hash = fields.Char(string='QR-Code hash')
    qrcode_url = fields.Char(string='QR-Code URL')
    metodo_pagamento = fields.Selection(metodos, string='Método de Pagamento')

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if self.model != '65':
            return errors
        if not self.company_id.partner_id.inscr_est:
            errors.append(u'Emitente / Inscrição Estadual')
        if len(self.company_id.id_token_csc or '') != 6:
            errors.append(u"Identificador do CSC inválido")
        if not len(self.company_id.csc or ''):
            errors.append(u"CSC Inválido")
        if self.partner_id.cnpj_cpf is None:
            errors.append(u"CNPJ/CPF do Parceiro inválido")
        if len(self.serie) == 0:
            errors.append(u"Número de Série da NFe Inválido")
        return errors

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        vals = super(InvoiceEletronic, self)\
            ._prepare_eletronic_invoice_values()
        if self.model != '65':
            return vals
        codigo_seguranca = {
            'cid_token': self.company_id.id_token_csc,
            'csc': self.company_id.csc,
        }
        vals['codigo_seguranca'] = codigo_seguranca
        if self.model == '65':
            vals['pagamento'] = self.metodo_pagamento
        return vals
