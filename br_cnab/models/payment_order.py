# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
import base64
from ..febraban.cnab import Cnab
from datetime import datetime
from datetime import time as dtime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFT

class ExportedPaymentOrder(models.Model):
    _name = 'exported.payment.order'

    file = fields.Binary('File', readonly=True)
    filename = fields.Char('File Name')
    exported_date = fields.Datetime('Exported Date')
    order_id = fields.Many2one('payment.order', 'Order')


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    cnab_file = fields.Binary('CNAB File', readonly=True)
    file_number = fields.Integer(u'Número sequencial do arquivo', readonly=1)
    data_emissao_cnab = fields.Datetime('Data de Emissão do CNAB')
    cnab_valido = fields.Boolean(u'CNAB Válido', readonly=1)
    exported_files = fields.One2many('exported.payment.order', 'order_id', string= u'File', readonly=True)

    @api.multi
    def gerar_cnab(self):
        if len(self.line_ids) < 1:
            raise UserError(
                u'Ordem de Cobrança não possui Linhas de Cobrança!')
        self.data_emissao_cnab = datetime.now()
        today = datetime.strftime(datetime.combine(datetime.now(), dtime.min),DTFT)
        exported_files = self.env['exported.payment.order'].search([('exported_date','>',today)])
        file_number = len(exported_files) + 1
        try:
            self.file_number = self.env['ir.sequence'].next_by_code('cnab.nsa')
        except:
            raise UserError(
                u'Número sequencial do arquivo must be integer')
        for order_id in self:
            order_id.validar_cnab()
            order = self.env['payment.order'].browse(order_id.id)
            cnab = Cnab.get_cnab(
                order.payment_mode_id.bank_account_id.bank_bic, '240')()
            remessa = cnab.remessa(order)
            if not self.name:
                self.name = 'CB%s%s.REM' % (
                    time.strftime('%d%m'), str(order.file_number))
            self.state = 'done'

            self.env['exported.payment.order'].create(
                {'file': base64.b64encode(remessa.encode('utf-8')), 'exported_date': datetime.now(),
                 'order_id': order.id,
                 'filename': 'CB%s%s.REM' % (
                     time.strftime('%d%m'), str(file_number))})
        return remessa

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
            if not order.payment_mode_id.company_id.legal_name:
                raise UserError(u'Legal Name not set for company')


            for line in order.line_ids:
                if line.state in ['r', 'rj']:
                    if not line.partner_id:
                        raise UserError(_("Partner not defined for %s" % line.name))
                    if line.partner_id.company_type == 'company' and not line.partner_id.legal_name:
                        raise UserError(
                            _(u"Razão Social not defined for %s" % line.partner_id.name))
                    if not line.partner_id.state_id:
                        raise UserError(_("State not defined for %s" % line.partner_id.name))
                    if not line.partner_id.state_id.code:
                        raise UserError(_("State code not defined for %s" % line.partner_id.name))
                        # max 15 chars
                    if not line.partner_id.district:
                        raise UserError(_("Bairro not defined for %s" % line.partner_id.name))
                    if not line.partner_id.zip:
                        raise UserError(_("CEP not defined for %s" % line.partner_id.name))
                    if not line.partner_id.city_id:
                        raise UserError(_("City not defined for %s" % line.partner_id.name))
                    if not line.partner_id.street:
                        raise UserError(_("Street not defined for %s" % line.partner_id.name))
                    if not line.move_line_id.nosso_numero:
                        raise UserError(_("Nosso numero not set for %s" % line.name))
                    # Itau code : 341 supposed not to be larger than 8 digits
                    if self.payment_mode_id.bank_account_id.bank_id.bic == '341':
                        try:
                            int(line.move_line_id.nosso_numero)
                        except:
                            raise UserError(
                                _(u"Nosso Número for move line %s must be integer" %line.move_line_id.name))


class PaymentOrderLine(models.Model):
    _inherit = "payment.order.line"

    state = fields.Selection([("r", "Rascunho"),
                              ("ag", "Aguardando"),
                              ("a", "Aceito"),  # code 2
                              ("e", "Enviado"),
                              ("rj", "Rejeitado"),  # code 3
                              ("p", "Pago"),  # code 6, 8
                              ("b", "Baixado"),  # code 5,9, 32
                              ("c", "Cancelado")],
                             default="r",
                             string=u"Situação", compute=False)


    # valid lines to export
    # invoice must be in Open Stage
    # line must be in Rascunho Stage
    @api.multi
    def validate_line_to_export(self):
        self.ensure_one()
        if self.move_id:
            invoice = self.env['account.invoice'].search([('move_id','=',self.move_id.id)])
            if len(invoice) and invoice.state in ['open'] and self.state== 'r':
                return True
        return False
