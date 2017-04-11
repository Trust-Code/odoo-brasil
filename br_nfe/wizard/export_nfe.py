# -*- coding: utf-8 -*-
# © 2016 Alessandro Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
import io
import re
import base64
# from datetime import date
import os.path
# from jinja2 import Environment, FileSystemLoader
from zipfile import ZipFile
from StringIO import StringIO
from odoo import api, fields, models


class ExportNfe(models.Model):
    _name = 'wizard.export.nfe'

    start_date = fields.Date(string=u"Data Inicial", required=True)
    end_date = fields.Date(string=u"Data Final", required=True)
    model = fields.Many2one(
        'br_account.fiscal.document', string='Documento')
    name = fields.Char('Nome', size=255)
    file = fields.Binary('Arquivo', readonly=True)
    state = fields.Selection(
        [('init', 'init'), ('done', 'done')],
        'state', readonly=True, default='init')

    def _invoice_vals(self, inv):
        tomador = {
            'cnpj_cpf': re.sub(
                '[^0-9]', '', inv.commercial_partner_id.cnpj_cpf or ''),
            'inscricao_municipal': re.sub(
                '[^0-9]', '', inv.commercial_partner_id.inscr_mun or
                '0000000'),
            'name': inv.commercial_partner_id.legal_name,
            'street': inv.commercial_partner_id.street,
            'number': inv.commercial_partner_id.number,
            'district': inv.commercial_partner_id.district,
            'zip': re.sub('[^0-9]', '', inv.commercial_partner_id.zip or ''),
            'city_code': '%s%s' % (
                inv.commercial_partner_id.state_id.ibge_code,
                inv.commercial_partner_id.city_id.ibge_code),
            'uf_code': inv.commercial_partner_id.state_id.code,
            'email': inv.partner_id.email,
            'phone': re.sub('[^0-9]', '', inv.partner_id.phone or ''),
        }
        items = []
        for line in inv.invoice_line_ids:
            items.append({
                'name': line.product_id.name,
                'CNAE': re.sub('[^0-9]', '',
                               inv.company_id.cnae_main_id.code or ''),
                'CST': '1',
                'aliquota': line.issqn_aliquota / 100,
                'valor_unitario': line.price_unit,
                'quantidade': int(line.quantity),
                'valor_total': line.price_subtotal,
            })
        emissao = fields.Date.from_string(inv.date_invoice)
        cfps = '9201'
        if inv.company_id.city_id.id != inv.commercial_partner_id.city_id.id:
            cfps = '9202'
        if inv.company_id.state_id.id != inv.commercial_partner_id.state_id.id:
            cfps = '9203'
        return {
            'tomador': tomador,
            'items': items,
            'data_emissao': emissao.strftime('%Y-%m-%dZ'),
            'cfps': cfps,
            'base_calculo': inv.issqn_base,
            'valor_issqn': inv.issqn_value,
            'valor_total': inv.amount_total
        }

    def _save_zip(self, xmls):
        tmp = '/tmp/odoo/nfse-export/'

        try:
            os.makedirs(tmp)
        except:
            pass
        zip_base64 = StringIO()
        zip_file = ZipFile(zip_base64, 'w')
        for xml in xmls:
            filename = os.path.join(tmp, xml['name'])
            with io.open(filename, 'w', encoding='utf8') as xml_file:
                xml_file.write(xml['content'])
            zip_file.write(filename, xml['name'])
        zip_file.close()
        zip_base64.seek(0)
        return base64.b64encode(zip_base64.getvalue())

    @api.multi
    def nfse_export(self):
        self.state = 'done'
        search_vals = []
        search_vals.append(('data_emissao', '>=', self.start_date))
        search_vals.append(('data_emissao', '<=', self.end_date))
        search_vals.append(('state', 'in', ['cancel', 'done', 'denied']))

        if self.model:
            search_vals.append(('model', 'in', [self.model.code]))

        invoice_ids = self.env['invoice.eletronic'].search(search_vals)
        xmls = []
        for invoice in invoice_ids:
            if not invoice.nfe_processada:
                invoice.generate_nfe_proc()
            xmls.append(base64.decodestring(invoice.nfe_processada))

        self.file = self._save_zip(xmls)
        self.name = 'xml_nfse_exportacao.zip'

        mod_obj = self.env['ir.model.data'].search(
            [('model', '=', 'ir.ui.view'),
             ('name', '=',
              'view_wizard_export_nfe')])

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(mod_obj.res_id, 'form')],
            'target': 'new',
        }
