
import re
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    from pycnab240.utils import decode_digitable_line, pretty_format_line
    from pycnab240.errors import DvNotValidError
except ImportError:
    _logger.error('Cannot import pycnab240', exc_info=True)


class WizardChangePayment(models.TransientModel):
    _name = 'wizard.change.payment'

    move_line_id = fields.Many2one('account.move.line', readonly=True)
    amount_total = fields.Float(string="Valor Total", readonly=True)
    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string="Modo de Pagamento")
    payment_type = fields.Selection(
        related="payment_mode_id.payment_type")
    linha_digitavel = fields.Char(string="Linha Digitável")
    partner_id = fields.Many2one(
        'res.partner', readonly=True, string="Parceiro")
    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência",
        domain="[('partner_id', '=', partner_id)]")
    date_maturity = fields.Date(string="Data de Vencimento")
    amount = fields.Float(string="Valor no boleto", readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(WizardChangePayment, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        move_line_ids = self.env['account.move.line'].browse(active_ids)
        partner_ids = move_line_ids.mapped('partner_id')
        if len(partner_ids) > 1:
            raise UserError(
                'É possível agendar apenas pagamentos para o mesmo cliente')
        elif len(partner_ids) == 1:
            res['partner_id'] = partner_ids[0].id
            res['amount_total'] = sum(
                [x.amount_residual for x in move_line_ids])
        return res

    @api.onchange('linha_digitavel')
    def _onchange_linha_digitavel(self):
        linha = re.sub('[^0-9]', '', self.linha_digitavel or '')
        if len(linha) in (47, 48):
            self.linha_digitavel = pretty_format_line(linha)
            vals = self._get_digitable_line_vals(linha)
            self.amount = vals.get('valor', 0.0)
            self.date_maturity = vals.get('vencimento')

    def _get_digitable_line_vals(self, digitable_line):
        try:
            return decode_digitable_line(digitable_line)
        except DvNotValidError:
            raise UserError("DV do código de Barras não confere!")

    def action_update_info(self):
        linha = re.sub('[^0-9]', '', self.linha_digitavel or '')
        if len(linha) not in (47, 48):
            raise UserError(
                'Tamanho da linha digitável inválido %s' % len(linha))
        vals = self._get_digitable_line_vals(linha)
        linha_digitavel = pretty_format_line(linha)
        barcode = vals['barcode']

        order_line = self.env['payment.order.line'].search(
            [('move_line_id', '=', self.move_line_id.id)])
        invoice = self.move_line_id.invoice_id
        if order_line and order_line.state == 'draft':
            order_line.write({
                'payment_mode_id': self.payment_mode_id.id,
                'linha_digitavel': linha_digitavel,
                'bank_account_id': self.bank_account_id.id,
                'date_maturity': self.date_maturity or order_line.date_maturity
            })
            self.move_line_id.write({
                'payment_mode_id': self.payment_mode_id.id,
                'date_maturity':
                self.date_maturity or self.move_line_id.date_maturity,
            })
        elif order_line:
            raise UserError(
                'O pagamento já foi processado! \
                Não é possível modificar informações aqui!')
        else:
            vals = invoice.prepare_payment_line_vals(self.move_line_id)
            vals['date_maturity'] = \
                self.date_maturity or self.move_line_id.date_maturity
            vals['linha_digitavel'] = linha_digitavel
            vals['barcode'] = barcode
            vals['bank_account_id'] = self.bank_account_id.id
            self.env['payment.order.line'].action_generate_payment_order_line(
                self.payment_mode_id, vals)
            if self.date_maturity:
                self.move_line_id.write({
                    'payment_mode_id': self.payment_mode_id.id,
                    'date_maturity': self.date_maturity,
                })
