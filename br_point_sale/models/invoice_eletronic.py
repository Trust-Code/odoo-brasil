# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import requests

from odoo import api, fields, models
from odoo.exceptions import UserError
from .account_journal import metodos


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    qrcode_hash = fields.Char(string='QR-Code hash')
    qrcode_url = fields.Char(string='QR-Code URL')
    metodo_pagamento = fields.Selection(metodos, string=u'Método de Pagamento')

    def valida_cep(self, cep):
        cep = re.sub(r"\D", "", cep)
        if len(cep) != 8:
            return False
        url = "\
http://cep.republicavirtual.com.br/web_cep.php?cep={}&formato=json"
        cep_url = url.format(cep)
        try:
            cep_request = requests.get(cep_url)
            cep_json = cep_request.json()
            if cep_json.get('resultado_txt',
                            False) == u'sucesso - cep completo':
                return True
            return False
        except requests.exceptions.Timeout:
            raise UserError(u"Desculpe, o serviço não está respondendo" +
                            u", este CEP não será validado agora.")

    @api.multi
    def _hook_validation(self):
        errors = super(InvoiceEletronic, self)._hook_validation()
        if not self.valida_cep(self.company_id.zip):
            errors.append('CEP da empresa inválido: %s' % self.company_id.zip)
        if not self.valida_cep(self.partner_id.zip):
            errors.append('CEP do parceiro inválido: %s' % self.partner_id.zip)
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
