import os
import io
import base64
import os.path
from zipfile import ZipFile
from odoo import api, fields, models


class ExportNfe(models.TransientModel):
    _name = 'wizard.export.nfe'
    _description = "Exporta NF-e"

    start_date = fields.Date(string=u"Data Inicial", required=True)
    end_date = fields.Date(string=u"Data Final", required=True)
    zip_file = fields.Binary('Arquivo', readonly=True)
    zip_file_name = fields.Char('Nome', size=255)
    state = fields.Selection(
        [('init', 'init'), ('done', 'done')],
        'state', readonly=True, default='init')

    def _save_zip(self, xmls):
        tmp = '/tmp/odoo/nfse-export/'
        try:
            os.makedirs(tmp)
        except:
            pass
        zip_base64 = io.BytesIO()
        zip_file = ZipFile(zip_base64, 'w')
        for xml in xmls:
            filename = os.path.join(tmp, xml['name'])
            with open(filename, 'w') as xml_file:
                xml_file.write(xml['content'])
            zip_file.write(filename, xml['name'])
        zip_file.close()
        zip_base64.seek(0)
        return base64.b64encode(zip_base64.getvalue())

    def nfse_export(self):
        search_vals = []
        search_vals.append(('data_emissao', '>=', self.start_date))
        search_vals.append(('data_emissao', '<=', self.end_date))
        search_vals.append(('state', 'in', ['cancel', 'done', 'denied', 'imported']))

        invoice_ids = self.env['eletronic.document'].search(search_vals)
        xmls = []
        for invoice in invoice_ids:
            if invoice.nfe_processada:
                xmls.append({
                    'content': base64.decodestring(
                        invoice.nfe_processada).decode(),
                    'name': invoice.nfe_processada_name
                })

        self.zip_file = self._save_zip(xmls)
        self.zip_file_name = 'xml_nfe_exportacao.zip'
        self.state = 'done'

        mod_obj = self.env['ir.model.data'].search(
            [('model', '=', 'ir.ui.view'),
             ('name', '=', 'view_wizard_export_nfe')])

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(mod_obj.res_id, 'form')],
            'target': 'new',
        }
