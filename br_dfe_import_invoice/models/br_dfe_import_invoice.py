# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SpedDFeQueryNSU(models.Model):

    _inherit = 'sped.dfe.query.nsu'

    doc_released = fields.Selection([('released', u'Documento Lançado'), ('not_released', u'Documento Não Lançado'),
                                     ('in_process', u'Lançamento em Andamento'),
                                     ('not_document', u'Não é um Documento a Ser Lançado')],
                                    string=u'Documento Lançado', compute='compute_doc_released', default=False)

    @api.depends('chave_nfe', 'nsu_type')
    def compute_doc_released(self):
        edocs = self.env['invoice.eletronic']
        edocs_import = self.env['br.account.invoice.import.wizard']
        for doc in self:
            if doc.nsu_type not in ['nfe', 'res_nfe']:
                doc.doc_released = 'not_document'
            else:
                search_edocs = edocs.search([('chave_nfe', '=', doc.chave_nfe)])
                search_docs_import = edocs_import.search([('chave_nfe', '=', doc.chave_nfe)])
                if len(search_edocs) > 0:
                    doc.doc_released = 'released'
                elif len(search_docs_import) > 0:
                    doc.doc_released = 'in_process'
                else:
                    doc.doc_released = 'not_released'


    @api.multi
    def import_xml_to_invoice(self):
        if self.nsu_type == 'nfe' and self.nfe_state == '1':

            invoice_import = self.env['br.account.invoice.import.wizard'].create({'xml_file': self.xml})
            invoice_import.validate_xml()
            invoice_import.validate_xml_file()

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'br.account.invoice.import.wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': invoice_import.id,
                'target': 'current',
            }

        elif self.nsu_type == 'res_nfe':
            for n in self.parent_id:
                if n.nsu_type == 'nfe' and n.nfe_state == '1':
                    invoice_import = self.env['br.account.invoice.import.wizard'].create({'xml_file': n.xml})
                    invoice_import.validate_xml_file()

                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'br.account.invoice.import.wizard',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_id': invoice_import.id,
                        'target': 'current',
                    }