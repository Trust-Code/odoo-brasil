import os
import io
import base64
import os.path
from zipfile import ZipFile
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

REPORT_NAME = {
    '05407': 'danfse',  # Florianopolis
    '06200': 'bh',  # Belo Horizonte
    '18800': 'ginfes', # Guarulhos
    '50308': 'danfe',  # Sao Paulo
}

class ExportNfe(models.TransientModel):
    _name = 'wizard.export.nfe'
    _description = "Exporta NF-e"

    start_date = fields.Date(string="Data Inicial", required=True)
    end_date = fields.Date(string="Data Final", required=True)
    zip_file = fields.Binary('Arquivo', readonly=True)
    zip_file_name = fields.Char('Nome', size=255)
    emitter = fields.Selection([('propria', 'Própria'), ('terceiros', 'Terceiros')], string="Emissão")
    edoc_type = fields.Selection([('entrada', 'Entrada'), ('saida', 'Saída')], string="Tipo de Operação")
    model = fields.Selection(
        [('nfe', '55 - NFe'),
         ('nfce', '65 - NFCe'),
         ('nfse', 'NFS-e - Nota Fiscal de Servico')],
        string='Modelo a exportar')

    state = fields.Selection(
        [('init', 'init'), ('done', 'done')],
        'state', readonly=True, default='init')

    def _save_zip(self, xmls, pdfs):
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
        for pdf in pdfs:
            filename = os.path.join(tmp, pdf['name'])
            with open(filename, 'wb') as pdf_file:
                pdf_file.write(pdf['content'])
            zip_file.write(filename, pdf['name'])
        zip_file.close()
        zip_base64.seek(0)
        return base64.b64encode(zip_base64.getvalue())

    def nfse_export(self):
        search_vals = []
        search_vals.append(('data_emissao', '>=', self.start_date))
        search_vals.append(('data_emissao', '<=', self.end_date))
        if self.emitter == 'propria':
            search_vals.append(('state', 'in', ['cancel', 'done', 'denied']))
        elif self.emitter == 'terceiros':
            search_vals.append(('state', '=', 'imported'))
        else:
            search_vals.append(('state', 'in', ['cancel', 'done', 'denied', 'imported']))
        if self.edoc_type:
            search_vals.append(('tipo_operacao', '=', self.edoc_type))
        if self.model:
            search_vals.append(('model', '=', self.model))

        invoice_ids = self.env['eletronic.document'].search(search_vals)
        xmls = []
        pdfs = []
        for invoice in invoice_ids:
            if invoice.nfe_processada:
                xmls.append({
                    'content': base64.decodestring(invoice.nfe_processada).decode(),
                    'name': invoice.nfe_processada_name
                })
            if invoice.model == 'nfse' and not invoice.nfse_pdf:
                danfe_name = "l10n_br_eletronic_document.main_template_br_nfse_danfpse"
                danfe_city = REPORT_NAME.get(invoice.company_id.city_id.l10n_br_ibge_code)
                if danfe_city:
                    danfe_name = 'l10n_br_eletronic_document.main_template_br_nfse_%s' % danfe_city

                danfe_report = self.env['ir.actions.report'].search(
                    [('report_name', '=', danfe_name)])
                if danfe_report:
                    report_service = danfe_report.xml_id
                    danfe, dummy = self.env.ref(report_service)._render_qweb_pdf([invoice.id])
                    report_name = safe_eval(danfe_report.print_report_name, {'object': invoice})
                    filename = "%s.%s" % (report_name, "pdf")
                    pdfs.append({
                        'content': danfe,
                        'name': filename
                    })
            if invoice.model == 'nfe':
                danfe_report = self.env['ir.actions.report'].search(
                    [('report_name', '=', 'l10n_br_eletronic_document.main_template_br_nfe_danfe')])
                report_service = danfe_report.xml_id
                danfe, dummy = self.env.ref(report_service)._render_qweb_pdf([invoice.id])
                report_name = safe_eval(danfe_report.print_report_name, {'object': invoice})
                report_name_clean = "".join([c for c in report_name if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
                filename = "%s.%s" % (report_name_clean, "pdf")
                pdfs.append({
                    'content': danfe,
                    'name': filename
                })

        self.zip_file = self._save_zip(xmls, pdfs)
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
