
import re
import ast
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
    amount_total = fields.Float(string="Valor Original", readonly=True)
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
    discount = fields.Float(string="Desconto")
    amount = fields.Float(string="Valor a pagar")
    line_ids = fields.Char(string="Line IDs")

    @api.model
    def default_get(self, fields):
        res = super(WizardChangePayment, self).default_get(fields)
        model = self.env.context.get('active_model', [])
        active_ids = self.env.context.get('active_ids', [])
        line_ids = self.env[model].browse(active_ids)
        res['line_ids'] = active_ids
        partner_ids = line_ids.mapped('partner_id')
        if len(partner_ids) > 1:
            raise UserError(
                'É possível agendar apenas pagamentos para o mesmo cliente')
        elif len(partner_ids) == 1:
            res['partner_id'] = partner_ids[0].id
            res['amount_total'] = sum(
                [abs(x.amount_residual) for x in line_ids])
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

    def _validate_information(self):
        errors = []
        if (self.amount_total - self.discount) != self.amount:
            errors += ['O valor a pagar deve ser: Valor original - Desconto']
        if self.payment_type in ['03', '04']:
            linha = re.sub('[^0-9]', '', self.linha_digitavel or '')
            if len(linha) not in (47, 48):
                errors += [
                    'Tamanho da linha digitável inválido %s' % len(linha)]
        if errors:
            msg = "\n".join(errors)
            raise UserError(msg)

    def get_barcode_information(self):
        if self.payment_type in ['03', '04']:
            linha = re.sub('[^0-9]', '', self.linha_digitavel or '')
            vals = self._get_digitable_line_vals(linha)
            linha_digitavel = pretty_format_line(linha)
            barcode = vals['barcode']
            return linha_digitavel, barcode
        return False, False

    def action_update_info(self):
        ids = ast.literal_eval(self.line_ids)
        lines = self.env[self.model].browse(ids)
        self.action_move_line(lines)

    def action_move_line(self, move_lines):
        linha_digitavel, barcode = self.get_barcode_information()
        order_lines = self.env['payment.order.line'].search(
            [('move_line_id', '=', move_lines.id)]) # agora são varias

        if order_lines and all(order_lines.state == 'draft'):
            for line in order_lines:
                line.write({
                    'payment_mode_id': self.payment_mode_id.id,
                    'linha_digitavel': linha_digitavel or '',
                    'bank_account_id': self.bank_account_id.id,
                    'discount_value': self.discount,
                    'date_maturity': self.date_maturity or line.date_maturity
                })
                self.move_line_id.write({
                    'payment_mode_id': self.payment_mode_id.id,
                    'date_maturity':
                        self.date_maturity or self.move_line_id.date_maturity,
                })
        elif order_lines:
            raise UserError(
                'Algum pagamento já foi processado! \
                Não é possível processa-lo novamente!')
        else:
            self.prepare_lines_from_invoice(
                barcode=barcode or False, linha_digitavel=linha_digitavel)

    def prepare_lines_from_invoice(self, barcode=False, linha_digitavel=False):
        invoice = self.move_line_id.invoice_id
        vals = invoice.prepare_payment_line_vals(self.move_line_id)
        vals['date_maturity'] = \
            self.date_maturity or self.move_line_id.date_maturity
        vals['bank_account_id'] = self.bank_account_id.id
        vals['discount_value'] = self.discount
        self.env['payment.order.line'].action_generate_payment_order_line(
            self.payment_mode_id, vals)
        if self.payment_type in ['03', '04']:
            vals['linha_digitavel'] = linha_digitavel
            vals['barcode'] = barcode
        if self.date_maturity:
            self.move_line_id.write({
                'payment_mode_id': self.payment_mode_id.id,
                'date_maturity': self.date_maturity,
            })
