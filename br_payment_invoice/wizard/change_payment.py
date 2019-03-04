
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

    @api.model
    def default_get(self, fields):
        res = super(WizardChangePayment, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        line_ids = self.env['account.move.line'].browse(active_ids)
        partner_ids = line_ids.mapped('partner_id')
        if len(partner_ids) > 1:
            raise UserError(
                _('É possível agendar apenas pagamentos para o mesmo cliente'))
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
            raise UserError(_("DV do código de Barras não confere!"))

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
        active_ids = self.env.context.get('active_ids', [])
        move_lines = self.env['account.move.line'].browse(active_ids)
        linha_digitavel, barcode = self.get_barcode_information()

        if len(move_lines) > 1:
            if not all([not x.l10n_br_order_line_id for x in move_lines]):
                raise UserError(_('Esta linha já possui pagamento agendado!'))

        order_line = False
        if len(move_lines) == 1 and move_lines[0].l10n_br_order_line_id:
            order_line = move_lines[0].l10n_br_order_line_id

        if order_line and order_line.state == 'draft':
            order_line.write({
                'payment_mode_id': self.payment_mode_id.id,
                'linha_digitavel': linha_digitavel or '',
                'bank_account_id': self.bank_account_id.id,
                'discount_value': self.discount,
                'date_maturity': self.date_maturity or order_line.date_maturity
            })
            self.move_line_id.write({
                'payment_mode_id': self.payment_mode_id.id,
                'date_maturity':
                    self.date_maturity or self.move_line_id.date_maturity,
            })
        elif order_line:
            raise UserError(
                _('Algum pagamento já foi processado! \
                  Não é possível processa-lo novamente!'))
        else:
            vals = self._prepare_vals(move_lines, linha_digitavel, barcode)
            order_line = self.env['payment.order.line'].\
                action_generate_payment_order_line(self.payment_mode_id, vals)
            move_lines.write({'l10n_br_order_line_id': order_line.id})

    def _prepare_vals(self, move_line_ids, linha_digitavel, barcode):
        vals = {
            'partner_id': self.partner_id.id,
            'amount_total': self.amount_total,
            'name': ', '.join([x.name for x in move_line_ids]),
            'partner_ref': ','.join([x.move_id.name for x in move_line_ids]),
            'bank_account_id': self.bank_account_id.id,
            'partner_acc_number': self.bank_account_id.acc_number,
            'partner_bra_number': self.bank_account_id.bra_number,
            'date_maturity': self.date_maturity,
            'discount_value': self.discount,
            'linha_digitavel': linha_digitavel,
            'barcode': barcode,
            'payment_mode_id': self.payment_mode_id.id,
        }
        if len(move_line_ids) == 1:
            vals['move_line_id'] = move_line_ids[0].id,
        return vals
