# © 2018 Danimar Ribeiro, Trustcode
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


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', "Modo de Pagamento", readonly=True,
        states={'draft': [('readonly', False)]})
    payment_type = fields.Selection(
        [('01', 'TED - Transferência Bancária'),
         ('02', 'DOC - Transferência Bancária'),
         ('03', 'Pagamento de Títulos'),
         ('04', 'Tributos com código de barras'),
         ('05', 'GPS - Guia de previdencia Social'),
         ('06', 'DARF Normal'),
         ('07', 'DARF Simples'),
         ('08', 'FGTS com Código de Barras'),
         ('09', 'ICMS')],
        string="Tipo de Operação", readonly=True,
        states={'draft': [('readonly', False)]})
    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência",
        domain="[('partner_id', '=', partner_id)]", readonly=True,
        states={'draft': [('readonly', False)]})

    linha_digitavel = fields.Char(
        string="Linha Digitável", readonly=True,
        states={'draft': [('readonly', False)]})
    barcode = fields.Char(
        'Barcode', compute="_compute_barcode", store=True, readonly=True)
    interest_value = fields.Float(
        'Interest Value', readonly=True,
        states={'draft': [('readonly', False)]})
    fine_value = fields.Float(
        'Fine Value', readonly=True, states={'draft': [('readonly', False)]})

    numero_parcela_icms = fields.Integer(
        'Número da parcela/notificação', readonly=True,
        states={'draft': [('readonly', False)]})

    divida_ativa_etiqueta = fields.Integer(
        'Dívida ativa/número da etiqueta', readonly=True,
        states={'draft': [('readonly', False)]})

    _sql_constraints = [
        ('account_voucher_barcode_uniq', 'unique (barcode)',
         _('O código de barras deve ser único!'))
    ]

    def get_order_line(self):
        for line in self.move_id.line_ids:
            if (line.l10n_br_order_line_id.autenticacao_pagamento):
                return line.l10n_br_order_line_id

    @api.multi
    def copy(self, default=None):
        default = default or {}
        default.update({'linha_digitavel': None, 'barcode': None})
        return super(AccountVoucher, self).copy(default=default)

    @api.depends('linha_digitavel')
    def _compute_barcode(self):
        for item in self:
            if not item.linha_digitavel:
                continue
            linha = re.sub('[^0-9]', '', item.linha_digitavel)
            if len(linha) not in (47, 48):
                raise UserError(
                    'Tamanho da linha digitável inválido %s' % len(linha))
            vals = self._get_digitable_line_vals(linha)
            item.barcode = vals['barcode']

    @api.onchange('linha_digitavel')
    def _onchange_linha_digitavel(self):
        linha = re.sub('[^0-9]', '', self.linha_digitavel or '')
        if len(linha) in (47, 48):
            self.linha_digitavel = pretty_format_line(linha)
            vals = self._get_digitable_line_vals(linha)
            if self.line_ids:
                self.line_ids[0].price_unit = vals.get('valor', 0.0)
            else:
                self.line_ids = [(0, 0, {
                    'quantity': 1.0,
                    'price_unit': vals.get('valor', 0.0)
                })]
            if vals.get('vencimento'):
                self.date_due = vals.get('vencimento')

    def _get_digitable_line_vals(self, digitable_line):
        try:
            return decode_digitable_line(digitable_line)
        except DvNotValidError:
            raise UserError("DV do código de Barras não confere!")

    @api.onchange('payment_mode_id')
    def _onchange_payment_mode_id(self):
        self.payment_type = self.payment_mode_id.payment_type

    @api.onchange('partner_id')
    def _onchange_payment_cnab_partner_id(self):
        bnk_account_id = self.env['res.partner.bank'].search(
            [('partner_id', '=', self.partner_id.commercial_partner_id.id)],
            limit=1)
        self.bank_account_id = bnk_account_id.id

    def _prepare_payment_order_vals(self):
        move_line_id = self.move_id.line_ids.filtered(
            lambda x: x.account_id == self.account_id)
        return {
            'numero_parcela_icms': self.numero_parcela_icms,
            'divida_ativa_etiqueta': self.divida_ativa_etiqueta,
            'partner_id': self.partner_id.id,
            'amount_total':
            self.amount - self.fine_value - self.interest_value,
            'name': self.number,
            'bank_account_id': self.bank_account_id.id,
            'partner_acc_number': self.bank_account_id.acc_number,
            'partner_bra_number': self.bank_account_id.bra_number,
            'move_line_id': move_line_id.id,
            'voucher_id': self.id,
            'date_maturity': self.date_due,
            'invoice_date': self.date,
            'barcode': self.barcode,
            'linha_digitavel': self.linha_digitavel,
            # TODO Ajustar o valor de multa e de juros
            # 'fine_value': self.fine_value,
            # 'interest_value': self.interest_value,
        }

    @api.multi
    def proforma_voucher(self):
        for item in self:
            if item.payment_mode_id and item.payment_mode_id.type == 'payable':
                item.validate_cnab_fields()
        res = super(AccountVoucher, self).proforma_voucher()
        for item in self:
            order_line_obj = self.env['payment.order.line']
            if item.payment_mode_id:
                order_line_obj.action_generate_payment_order_line(
                    item.payment_mode_id,
                    item._prepare_payment_order_vals())
        return res

    def validate_cnab_fields(self):
        if not self.date_due:
            raise UserError(_("Please select a Due Date for the payment"))

    def create_interest_fine_line(self, line_type, vals):
        account_id = self.env['ir.config_parameter'].sudo().get_param(
            'br_payment_cnab.{}_account_id'.format(line_type))
        if not account_id:
            raise UserError(_(
                "Please configure the interest and fine accounts"))
        line_vals = (0, 0, {
            'name': _('Fine Line') if line_type == 'fine' else _(
                'Interest Line'),
            'quantity': 1,
            'price_unit': vals.get('{}_value'.format(line_type)),
            'account_id': account_id
        })
        if vals.get('line_ids'):
            vals['line_ids'].append(line_vals)
        else:
            vals.update(line_ids=[line_vals])
        return vals

    @api.multi
    def write(self, vals):
        if vals.get('interest_value'):
            vals = self.create_interest_fine_line('interest', vals)
        if vals.get('fine_value'):
            vals = self.create_interest_fine_line('fine', vals)
        res = super(AccountVoucher, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        if vals.get('interest_value', 0) > 0:
            vals = self.create_interest_fine_line('interest', vals)
        if vals.get('fine_value', 0) > 0:
            vals = self.create_interest_fine_line('fine', vals)
        res = super(AccountVoucher, self).create(vals)
        return res
