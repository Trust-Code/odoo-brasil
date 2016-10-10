# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductFiscalClassificationWizard(models.TransientModel):
    _name = 'product.fiscal.classification.wizard'

    product_fiscal_class_csv = fields.Binary(string="Arquivo CSV")

    @api.multi
    def import_ncm(self):
        if not self.product_fiscal_class_csv:
            raise UserError(u'Nenhum Arquivo Selecionado!')
        ncm_csv = base64.decodestring(self.product_fiscal_class_csv)
        ncm_csv_lines = ncm_csv.split('\r\n')
        for line in ncm_csv_lines[1:-1]:
            col = line.split(';')
            code = str(col[0])
            if len(code.zfill(4)) == 4:
                try:
                    code = code.zfill(4)
                    code = code[:2] + '.' + code[2:]
                    service = self.env['br_account.service.type'].search(
                        [('code', '=', code)])
                    service.update({
                        'federal_nacional': col[4],
                        'federal_importado': col[5],
                        'estadual_imposto': col[6],
                        'municipal_imposto': col[7],
                    })
                except Exception as e:
                    _logger.error(e.message, exc_info=True)
            elif len(code.zfill(8)) == 8:
                code = code.zfill(8)
                code = code[:4] + '.' + code[4:6] + '.' + code[6:]
                try:
                    service = self.env['product.fiscal.classification'].search(
                        [('code', '=', code)])
                    service.update({
                        'federal_nacional': col[4],
                        'federal_importado': col[5],
                        'estadual_imposto': col[6],
                        'municipal_imposto': col[7],
                    })
                except Exception as e:
                    _logger.error(e.message, exc_info=True)
