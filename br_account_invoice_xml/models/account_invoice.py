# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_edoc_vals(self, inv, inv_lines):
        res = super(AccountInvoice, self)._prepare_edoc_vals(inv, inv_lines)
        if inv.product_document_id.emissao_doc == '2':
            res['emissao_doc'] = '2'
            res['state'] = 'done'
            if inv.total_despesas < 0.0:
                res['valor_desconto'] = inv.total_despesas * (-1)
                res['valor_despesas'] = 0.0
        return res

    
    def _prepare_edoc_item_vals(self, invoice_line):
        vals = super(AccountInvoice, self)._prepare_edoc_item_vals(invoice_line)
        if invoice_line.outras_despesas < 0.0:
            vals['desconto'] = invoice_line.outras_despesas * (-1)
            vals['outras_despesas'] = 0.0
            vals['valor_liquido'] = vals['valor_liquido'] - vals['desconto']
        return vals
        
            
    @api.multi
    def import_xml_nfe_entrada(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "import.xml.wizard",
            "views": [[False, "form"]],
            "name": "Importar NFe",
            "target": "new",
            "context": {'invoice_id': self.id, 'tipo':self.nfe_modelo},
        }


class BrAccountFiscalDocument(models.Model):
    _inherit = 'br_account.fiscal.document'

    emissao_doc = fields.Selection([
        ('1', u'1 - Emissão Própria'),
        ('2', u'2 - Terceiros'),
        ], u'Indicador do Emitente', default='1')
