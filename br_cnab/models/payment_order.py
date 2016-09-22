# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
import time
import base64
from ..febraban.cnab import Cnab


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    cnab_file = fields.Binary('CNAB File', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Cliente")
    file_number = fields.Integer(u'Número sequencial do arquivo', readonly=1)

    @api.multi
    def gerar_cnab(self):
        self.file_number = self.env['ir.sequence'].next_by_code('cnab.nsa')
        for order_id in self:

            order = self.env['payment.order'].browse(order_id.id)
            cnab = Cnab.get_cnab(
                order.payment_mode_id.bank_account_id.bank_bic,
                order.payment_mode_id.payment_type_id.code)()
            remessa = cnab.remessa(order)
            suf_arquivo = 'ABX'  # order.get_next_sufixo()

            if order.payment_mode_id.payment_type_id.code == '240':
                self.name = 'CB%s%s.REM' % (
                    time.strftime('%d%m'), str(order.file_number))
            elif order.payment_mode_id.payment_type_id.code == '400':
                self.name = 'CB%s%s.REM' % (
                    time.strftime('%d%m'), str(suf_arquivo))
            elif order.payment_mode_id.payment_type_id.code == '500':
                self.name = 'PG%s%s.REM' % (
                    time.strftime('%d%m'), str(order.file_number))
            self.state = 'done'
            self.cnab_file = base64.b64encode(remessa)

            self.env['ir.attachment'].create({
                'name': self.name,
                'datas': self.cnab_file,
                'datas_fname': self.name,
                'description': 'Arquivo CNAB 240',
                'res_model': 'payment.order',
                'res_id': order_id
            })
