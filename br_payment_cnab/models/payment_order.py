# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import base64
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

try:
    from ..bancos import santander, sicoob
except ImportError:
    _logger.debug('Cannot import bancos.')


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    def select_bank_cnab(self, code):
        banks = {
            '756': sicoob.Sicoob240(self),
            '033': santander.Santander240(self),
            # '641': Itau240(self),
            # '237': Bradesco240(self)
        }
        bank = banks.get(code)
        if not bank:
            raise UserError(_("You can't generate cnab for the bank {} yet!"
                              .format(code)))
        return bank

    def get_file_number(self):
        if all(item.payment_information_id.l10n_br_environment == 'production'
               for item in self.line_ids):
            return self.env['ir.sequence'].next_by_code('cnab.nsa')
        else:
            return '1'

    def action_generate_payable_cnab(self):
        self.file_number = self.get_file_number()
        self.data_emissao_cnab = datetime.now()
        cnab = self.select_bank_cnab(str(
            self.payment_mode_id.bank_account_id.bank_id.bic))
        cnab.create_cnab(self.line_ids)
        self.line_ids.write({'state': 'sent'})
        self.cnab_file = base64.b64encode(cnab.write_cnab())
        self.name = self.env['ir.sequence'].next_by_code('payment.cnab.name')


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    payment_information_id = fields.Many2one(
        'l10n_br.payment_information', string="Payment Information")

    invoice_date = fields.Date('Data da Fatura')

    @api.depends('payment_information_id')
    def _compute_final_value(self):
        for item in self:
            payment = item.payment_information_id
            desconto = payment.rebate_value + payment.discount_value
            acrescimo = payment.fine_value + payment.interest_value
            item.value_final = (item.amount_total - desconto + acrescimo)

    value_final = fields.Float(
        string="Final Value", compute="_compute_final_value",
        digits=(18, 2), readonly=True)

    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência")

    def get_opration_code(self, payment_mode):
        if payment_mode.payment_type == '01':
            return '018'
        elif payment_mode.payment_type == '02':
            return '700'

    def get_payment_order(self, payment_mode):
        order_name = self.env['ir.sequence'].next_by_code('payment.order')
        payment_order = self.env['payment.order'].search([
            ('state', '=', 'draft'),
            ('src_bank_account_id', '=', payment_mode.bank_account_id.id),
            ('type', '=', 'payable')], limit=1)
        if not payment_order:
            payment_order = payment_order.sudo().create({
                'name': order_name or '',
                'user_id': self.env.user.id,
                'payment_mode_id': payment_mode.id,
                'src_bank_account_id': payment_mode.bank_account_id.id,
                'state': 'draft',
                'type': 'payable',
            })
        return payment_order

    def get_service_type(self, payment_mode):
        if payment_mode.finality_ted == '05':
            return '20'
        if payment_mode.payment_type in ('04', '05', '06', '07', '08', '09'):
            return '22'

    def get_information_vals(self, payment_mode_id, vals):
        return {
            'payment_type': payment_mode_id.payment_type,
            'finality_ted': payment_mode_id.finality_ted,
            'mov_finality': payment_mode_id.mov_finality,
            'operation_code': self.get_opration_code(payment_mode_id),
            'codigo_receita': payment_mode_id.codigo_receita,
            'service_type': self.get_service_type(payment_mode_id),
            'barcode': vals.pop('barcode'),
            'fine_value': vals.pop('fine_value'),
            'interest_value': vals.pop('interest_value'),
            'numero_referencia': payment_mode_id.numero_referencia,
            'l10n_br_environment': payment_mode_id.l10n_br_environment
        }

    def action_generate_payment_order_line(self, payment_mode, **vals):
        payment_order = self.get_payment_order(payment_mode)
        info_vals = self.get_information_vals(payment_mode, vals)
        information_id = self.env['l10n_br.payment_information'].sudo().create(
            info_vals)
        line_vals = {
            'payment_mode_id': payment_mode.id,
            'payment_information_id': information_id.id,
            'payment_order_id': payment_order.id,
            'nosso_numero': payment_mode.nosso_numero_sequence
            .next_by_id(),
        }
        line_vals.update(vals)
        self.sudo().create(line_vals)

    def action_aprove_payment_line(self):
        # TODO Check if user has access
        self.state = 'approved'

    def action_open_edit_wizard(self):
        pass

    def action_view_more_info(self):
        return {
            'name': 'Detailed Payment Information',
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_br.payment_information',
            'res_id': self.payment_information_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }
