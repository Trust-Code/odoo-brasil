# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    from pycnab240.utils import decode_digitable_line, pretty_format_line
    from pycnab240.errors import DvNotValidError
except ImportError:
    _logger.error('Cannot import pycnab240', exc_info=True)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_br_linha_digitavel = fields.Char(
        string="Linha Digitável", readonly=True,
        states={'draft': [('readonly', False)]})
    l10n_br_barcode = fields.Char(
        'Barcode', compute="_compute_barcode", store=True, readonly=True)
    l10n_br_payment_type = fields.Selection(
        related="payment_mode_id.payment_type", readonly=True)
    l10n_br_bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência",
        domain="[('partner_id', '=', partner_id)]", readonly=True,
        states={'draft': [('readonly', False)]})

    @api.depends('l10n_br_linha_digitavel')
    def _compute_barcode(self):
        for item in self:
            if not item.l10n_br_linha_digitavel:
                continue
            linha = re.sub('[^0-9]', '', item.l10n_br_linha_digitavel)
            if len(linha) not in (47, 48):
                raise UserError(
                    _('Tamanho da linha digitável inválido %s') % len(linha))
            vals = self._get_digitable_line_vals(linha)
            item.l10n_br_barcode = vals['barcode']

    @api.onchange('l10n_br_linha_digitavel')
    def _onchange_linha_digitavel(self):
        linha = re.sub('[^0-9]', '', self.l10n_br_linha_digitavel or '')
        if len(linha) in (47, 48):
            self.l10n_br_linha_digitavel = pretty_format_line(linha)
            vals = self._get_digitable_line_vals(linha)
            if self.invoice_line_ids:
                self.invoice_line_ids[0].price_unit = vals.get('valor', 0.0)
            else:
                self.invoice_line_ids = [(0, 0, {
                    'quantity': 1.0,
                    'price_unit': vals.get('valor', 0.0)
                })]
            if vals.get('vencimento'):
                self.date_due = vals.get('vencimento')

    def _get_digitable_line_vals(self, digitable_line):
        try:
            return decode_digitable_line(digitable_line)
        except DvNotValidError:
            raise UserError(_("DV do código de Barras não confere!"))

    def prepare_payment_line_vals(self, move_line_id):
        return {
            'partner_id': self.partner_id.id,
            'amount_total': abs(move_line_id.amount_residual),
            'name': self.number,
            'partner_ref': self.reference,
            'bank_account_id': self.l10n_br_bank_account_id.id,
            'partner_acc_number': self.l10n_br_bank_account_id.acc_number,
            'partner_bra_number': self.l10n_br_bank_account_id.bra_number,
            'move_line_id': move_line_id.id,
            'date_maturity': move_line_id.date_maturity,
            'invoice_date': move_line_id.date,
            'invoice_id': self.id,
            'linha_digitavel': self.l10n_br_linha_digitavel,
            'barcode': self.l10n_br_barcode,
        }

    def get_order_line(self):
        for line in self.move_id.line_ids:
            if (line.l10n_br_order_line_id.autenticacao_pagamento):
                return line.l10n_br_order_line_id

    def check_create_payment_line(self):
        if self.payment_mode_id.type != 'payable':
            return
        if self.l10n_br_payment_type in ('03'):  # Boletos
            if len(self.payable_move_line_ids) > 1 and self.l10n_br_barcode:
                raise UserError(
                    'A fatura possui mais de uma parcela, preencha a \
                    linha digitável diretamente nos vencimentos após \
                    a validação')
        elif self.l10n_br_payment_type in ('01', '02'):  # Depósitos
            if not self.l10n_br_bank_account_id:
                raise UserError(
                    _('A conta bancária para depósito é obrigatório'))
        else:
            raise UserError(_('Para tributos utilize os recibos de compra'))

        for item in self.payable_move_line_ids:
            if not item.payment_mode_id:
                return
            vals = self.prepare_payment_line_vals(item)
            line_obj = self.env['payment.order.line'].with_context({})
            line_obj.action_generate_payment_order_line(
                item.payment_mode_id, vals)

    @api.multi
    def action_move_create(self):
        super(AccountInvoice, self).action_move_create()
        for item in self:
            item.check_create_payment_line()
