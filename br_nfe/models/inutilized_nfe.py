# -*- coding: utf-8 -*-
# © 2016 Alessandro Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from datetime import datetime

from odoo import fields, models


class InutilizedNfe(models.Model):
    _name = 'invoice.eletronic.inutilized'

    name = fields.Char('Nome', readonly=True, required=True)
    numero_inicial = fields.Integer('Numero Inicial')
    numero_final = fields.Integer('Numero Final')
    justificativa = fields.Text('Justificativa')
    state = fields.Selection([
        ('draft', 'Provisório'), ('done', 'Enviado'), ('error', 'Erro')],
        string=u'State', default='draft', readonly=True)

    def _create_attachment(self, prefix, event, data):
        file_name = '%s-%s.xml' % (
            prefix, datetime.now().strftime('%Y-%m-%d-%H-%M'))
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(data),
                'datas_fname': file_name,
                'description': u'',
                'res_model': 'invoice.eletronic.inutilized',
                'res_id': event.id
            })

