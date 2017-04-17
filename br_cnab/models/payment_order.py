# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
import base64
from ..febraban.cnab import Cnab
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    cnab_file = fields.Binary('CNAB File', readonly=True)
    file_number = fields.Integer(u'Número sequencial do arquivo', readonly=1)
    data_emissao_cnab = fields.Datetime('Data de Emissão do CNAB')
    cnab_valido = fields.Boolean(u'CNAB Válido', readonly=1)

    @api.multi
    def gerar_cnab(self):
        if len(self.line_ids) < 1:
            raise UserError(
                u'Ordem de Cobrança não possui Linhas de Cobrança!')
        self.data_emissao_cnab = datetime.now()
        try:
            self.file_number = self.env['ir.sequence'].next_by_code('cnab.nsa')
        except:
            raise UserError(
                u'Número sequencial do arquivo must be integer')
        for order_id in self:
            order = self.env['payment.order'].browse(order_id.id)
            cnab = Cnab.get_cnab(
                order.payment_mode_id.bank_account_id.bank_bic, '240')()
            remessa = cnab.remessa(order)

            self.name = 'CB%s%s.REM' % (
                time.strftime('%d%m'), str(order.file_number))
            self.state = 'done'
            self.cnab_file = base64.b64encode(remessa.encode('utf-8'))

            self.env['ir.attachment'].create({
                'name': self.name,
                'datas': self.cnab_file,
                'datas_fname': self.name,
                'description': 'Arquivo CNAB 240',
                'res_model': 'payment.order',
                'res_id': order_id
            })

    @api.multi
    def validar_cnab(self):
        for order in self:
            if not order.payment_mode_id.bank_account_id:
                raise UserError(
                    u"Bank Account not set")
                if not order.payment_mode_id.bank_account_id.acc_number:
                    raise UserError(u'Account Number not set')
                if not order.payment_mode_id.bank_account_id.acc_number_dig:
                    raise UserError(u'Digito Conta not set')
                if not order.payment_mode_id.bank_account_id.bra_number:
                    raise UserError(u'Agência not set')
                if not order.payment_mode_id.bank_account_id.bra_number_dig:
                    raise UserError(u'Dígito Agência not set')

            for line in order.line_ids:
                if not line.partner_id:
                    raise UserError(_("Partner not defined for %s" % line.name))
                if not line.partner_id.legal_name:
                    raise UserError(
                        _(u"Razão Social not defined for %s" % line.partner_id.name))
                if not line.partner_id.state_id:
                    raise UserError(_("Partner's state not defined"))
                if not line.partner_id.state_id.code:
                    raise UserError(_("Partner's state code not defined"))
                    # max 15 chars
                if not line.partner_id.district:
                    raise UserError(_("Partner's bairro not defined"))
                if not line.partner_id.zip:
                    raise UserError(_("Partner's CEP not defined"))
                if not line.partner_id.city_id:
                    raise UserError(_("Partner's city not defined"))
                if not line.partner_id.street:
                    raise UserError(_("Partner's street not defined"))

                # Itau code : 341 supposed not to be larger than 8 digits
                if self.payment_mode_id.bank_account_id.bank_id.bic == '341':
                    try:
                        int(line.move_line_id.nosso_numero.split('/')[1].split('-')[0])
                    except:
                        raise UserError(
                            _(u"Nosso Número for move line must be in format xx/xxxxxxxx-x, digits between / and - must be integers"))

