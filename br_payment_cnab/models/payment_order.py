# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import base64
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

try:
    from ..bancos import santander, sicoob, itau
except ImportError:
    _logger.debug('Cannot import bancos.')


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    def select_bank_cnab(self, code):
        banks = {
            '756': sicoob.Sicoob240(self),
            '033': santander.Santander240(self),
            '341': itau.Itau240(self),
            # '237': Bradesco240(self)
        }
        bank = banks.get(code)
        if not bank:
            raise UserError(
                _("You can't generate cnab for the bank {} yet!".format(code)))
        return bank

    def get_file_number(self):
        if all(item.payment_information_id.l10n_br_environment == 'production'
               for item in self.line_ids):
            return self.env['ir.sequence'].next_by_code('cnab.nsa')
        else:
            return '1'

    def action_approve_all(self):
        lines = self.line_ids.filtered(lambda x: x.state == 'draft')
        lines.write({'state': 'approved'})

    def action_generate_payable_cnab(self):
        lines = self.line_ids.filtered(
            lambda x: x.state in ('approved', 'sent'))
        if not lines:
            raise UserError('Nenhum pagamento aprovado!')

        self.file_number = self.get_file_number()
        self.data_emissao_cnab = datetime.now()
        cnab = self.select_bank_cnab(str(
            self.src_bank_account_id.bank_id.bic))
        cnab.create_cnab(lines)
        lines.write({'state': 'sent'})
        self.cnab_file = base64.b64encode(cnab.write_cnab())
        self.name = self.env['ir.sequence'].next_by_code(
            'payment.cnab.name')

        remaining_lines = self.line_ids - lines
        if remaining_lines:
            new_order = self.copy({
                'data_emissao_cnab': False, 'cnab_file': False,
                'file_number': 0,
                'name': self.env['ir.sequence'].next_by_code(
                    'payment.order')
            })
            remaining_lines.write({'payment_order_id': new_order.id})


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    journal_id = fields.Many2one('account.journal', string="Diário")
    payment_information_id = fields.Many2one(
        'l10n_br.payment_information', string="Payment Information")

    invoice_date = fields.Date('Data da Fatura')

    # Pagamento de Títulos Bancários
    def validate_payment_type_03(self, payment_mode, vals):
        # Pagamento mensal pode salvar sem código de barras
        if not payment_mode.one_time_payment:
            if not vals.get('barcode'):
                raise UserError('Código de barras obrigatório')
            if len(vals['barcode']) < 47 or len(vals['barcode']) > 48:
                raise UserError(
                    'Código de barras deve possuir 47 ou 48 dígitos')

    # Tributos com códigos de barras
    def validate_payment_type_04(self, payment_mode, vals):
        if not vals.get('barcode'):
            raise UserError('Código de barras obrigatório')
        if len(vals['barcode']) < 47 or len(vals['barcode']) > 48:
            raise UserError('Código de barras deve possuir 47 ou 48 dígitos')

    def validate_information(self, payment_mode, vals):
        validate = getattr(
            self, 'validate_payment_type_%s' %
            payment_mode.payment_type, False)
        if validate:
            validate(payment_mode, vals)

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

    def get_operation_code(self, payment_mode):
        if payment_mode.payment_type == '01':
            return '018'
        elif payment_mode.payment_type == '02':
            return '700'

    def get_payment_order(self, payment_mode):
        order_name = self.env['ir.sequence'].next_by_code('payment.order')
        payment_order = self.env['payment.order'].search([
            ('state', '=', 'draft'),
            ('src_bank_account_id', '=',
             payment_mode.journal_id.bank_account_id.id),
            ('type', '=', 'payable')], limit=1)
        if not payment_order:
            payment_order = payment_order.sudo().create({
                'name': order_name or '',
                'user_id': self.env.user.id,
                'payment_mode_id': payment_mode.id,
                'src_bank_account_id':
                payment_mode.journal_id.bank_account_id.id,
                'state': 'draft',
                'type': 'payable',
            })
        return payment_order

    def get_service_type(self, payment_mode):
        if payment_mode.payment_type in ('04', '05', '06', '07', '08', '09'):
            return '22'
        else:
            return payment_mode.service_type

    def get_information_vals(self, payment_mode_id, vals):
        return {
            'payment_type': payment_mode_id.payment_type,
            'mov_finality': payment_mode_id.mov_finality,
            'operation_code': self.get_operation_code(payment_mode_id),
            'codigo_receita': payment_mode_id.codigo_receita,
            'service_type': self.get_service_type(payment_mode_id),
            'barcode': vals.get('barcode'),
            'fine_value': vals.get('fine_value'),
            'interest_value': vals.get('interest_value'),
            'numero_referencia': payment_mode_id.numero_referencia,
            'l10n_br_environment': payment_mode_id.l10n_br_environment
        }

    def action_generate_payment_order_line(self, payment_mode, **vals):
        self.validate_information(payment_mode, vals)
        payment_order = self.get_payment_order(payment_mode)
        info_vals = self.get_information_vals(payment_mode, vals)
        information_id = self.env['l10n_br.payment_information'].sudo().create(
            info_vals)
        journal = payment_mode.journal_id
        line_vals = {
            'payment_mode_id': payment_mode.id,
            'journal_id': payment_mode.journal_id.id,
            'currency_id': payment_mode.journal_id.currency_id.id or
            payment_mode.journal_id.company_id.currency_id.id,
            'payment_information_id': information_id.id,
            'payment_order_id': payment_order.id,
            'emission_date': date.today(),
            'nosso_numero': journal.l10n_br_sequence_nosso_numero.next_by_id(),
        }
        line_vals.update(vals)
        self.sudo().create(line_vals)

    def action_aprove_payment_line(self):
        # TODO Check if user has access
        self.state = 'approved'

    def create_move_and_reconcile(self, order_line):
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': order_line.journal_id.id,
            'company_id': order_line.journal_id.company_id.id,
            'date': date.today(),
            'ref': order_line.name,
        })
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        counterpart_aml_dict = {
            'name': order_line.name,
            'move_id': move.id,
            'partner_id': order_line.partner_id.id,
            'debit': order_line.amount_total,
            'credit': 0.0,
            'currency_id': order_line.currency_id.id,
            'account_id': order_line.move_line_id.account_id.id,
        }
        liquidity_aml_dict = {
            'name': order_line.name,
            'move_id': move.id,
            'partner_id': order_line.partner_id.id,
            'debit': 0.0,
            'credit': order_line.amount_total,
            'currency_id': order_line.currency_id.id,
            'account_id': order_line.journal_id.default_debit_account_id.id,
        }
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        aml_obj.create(liquidity_aml_dict)
        move.post()
        (counterpart_aml + order_line.move_line_id).reconcile()
        return move

    def mark_order_line_paid(self):
        bank_account_ids = self.mapped('src_bank_account_id')
        for account in bank_account_ids:
            order_lines = self.filtered(
                lambda x: x.src_bank_account_id == account)
            journal_id = self.env['account.journal'].search(
                [('bank_account_id', '=', account.id)], limit=1)

            statement_id = self.env['l10n_br.payment.statement'].create({
                'name': '0001/Manual',
                'date': date.today(),
                'state': 'validated',
                'journal_id': journal_id.id,
            })
            for item in order_lines:
                move_id = self.create_move_and_reconcile(item)
                self.env['l10n_br.payment.statement.line'].create({
                    'statement_id': statement_id.id,
                    'date': date.today(),
                    'name': '0001/Manual',
                    'partner_id': item.partner_id.id,
                    'ref': item.name,
                    'amount': item.value_final,
                    'move_id': move_id.id,
                })
            order_lines.write({'state': 'paid'})

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
