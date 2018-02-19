# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
import base64
from ..febraban.cnab import Cnab
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    cnab_file = fields.Binary('CNAB File', readonly=True)
    file_number = fields.Integer(u'Número sequencial do arquivo', readonly=1)
    data_emissao_cnab = fields.Datetime('Data de Emissão do CNAB')
    state = fields.Selection(
        [('draft', 'Rascunho'),
         ('cancel', 'Cancelado'),
         ('pending', 'Pendente'),
         ('open', 'Confirmado'),
         ('done', 'Fechado')],
        string=u"Situação",
        compute='_compute_state',
        store=True)

    @api.multi
    @api.depends('line_ids', 'cnab_file')
    def _compute_state(self):
        for item in self:
            if any(line.state == 'rejected' for line in item.line_ids):
                item.state = 'pending'
            elif all(line.state == 'baixa' for line in item.line_ids):
                item.state = 'cancel'
            elif all(line.state not in ('baixa', 'draft', 'rejected') for line
                     in item.line_ids):
                item.state = 'open'
            elif item.cnab_file:
                item.state = 'done'
            else:
                item.state = 'draft'

    @api.multi
    def gerar_cnab(self):
        if len(self.line_ids) < 1:
            raise UserError(
                u'Ordem de Cobrança não possui Linhas de Cobrança!')
        self.data_emissao_cnab = datetime.now()
        self.file_number = self.env['ir.sequence'].next_by_code('cnab.nsa')
        for order_id in self:
            order = self.env['payment.order'].browse(order_id.id)
            cnab = Cnab.get_cnab(
                order.payment_mode_id.bank_account_id.bank_bic, '240')()
            remessa = cnab.remessa(order)

            self.name = 'CNAB%s%s.REM' % (
                time.strftime('%m%d'), str(order.file_number))
            self.cnab_file = base64.b64encode(remessa)

            self.env['ir.attachment'].create({
                'name': self.name,
                'datas': self.cnab_file,
                'datas_fname': self.name,
                'description': 'Arquivo CNAB 240',
                'res_model': 'payment.order',
                'res_id': order_id
            })
