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

    payment_information_id = fields.Many2one(
        'l10n_br.payment_information', string="Payment Information",
        readonly=True)

    linha_digitavel = fields.Char(string="Linha Digitável")
    barcode = fields.Char('Código de Barras')
    invoice_date = fields.Date('Data da Fatura')
    cnab_code = fields.Char(string="Código Retorno")
    cnab_message = fields.Char(string="Mensagem Retorno")
    value_final = fields.Float(
        string="Final Value", compute="_compute_final_value",
        digits=(18, 2), readonly=True)

    bank_account_id = fields.Many2one(
        'res.partner.bank', string="Conta p/ Transferência")

    partner_acc_number = fields.Char(
        string="Conta do Favorecido",
        readonly=True)

    partner_bra_number = fields.Char(
        string="Agência do Favorecido",
        readonly=True)

    _sql_constraints = [
        ('payment_order_line_barcode_uniq', 'unique (barcode)',
         _('O código de barras deve ser único!'))
    ]

    def validate_partner_data(self, vals):
        errors = []
        if "partner_id" not in vals:
            errors += ['Selecione o parceiro!']
            return errors
        partner = self.env['res.partner'].browse(vals['partner_id'])
        if not partner.cnpj_cpf:
            errors += ['CNPJ/CPF do parceiro é obrigatório!']
        if not partner.legal_name and not partner.name:
            errors += ['Nome e/ou Razão Social é obrigatório!']
        if not partner.zip:
            errors += ['CEP do parceiro é obrigatório!']
        if not partner.street:
            errors += ['Endereço do parceiro é obrigatório!']
        if not partner.country_id:
            errors += ['País do parceiro é obrigatório!']
        if not partner.state_id:
            errors += ['Estado do parceiro é obrigatório!']
        if not partner.city_id:
            errors += ['Cidade do parceiro é obrigatório!']
        return errors

    def validate_bank_account(self, vals):
        errors = []
        if "bank_account_id" not in vals or not vals["bank_account_id"]:
            errors += ['Selecione a conta bancária para transferência!']
            return errors
        bnk_account = self.env['res.partner.bank'].browse(
            vals["bank_account_id"])
        if not bnk_account.bank_id:
            errors += ['Selecione o banco na conta bancária!']
        if not bnk_account.acc_number:
            errors += ['Preencha o número da conta bancária!']
        if not bnk_account.acc_number_dig:
            errors += ['Preencha o digito verificador da conta bancária!']
        if not bnk_account.bra_number:
            errors += ['Preencha a agência na conta bancária!']
        return errors

    # DOC
    def validate_payment_type_01(self, payment_mode, vals):
        errors = []
        errors += self.validate_partner_data(vals)
        errors += self.validate_bank_account(vals)
        return errors

    # TED
    def validate_payment_type_02(self, payment_mode, vals):
        errors = []
        errors += self.validate_partner_data(vals)
        errors += self.validate_bank_account(vals)
        return errors

    # Pagamento de Títulos Bancários
    def validate_payment_type_03(self, payment_mode, vals):
        # Pagamento mensal pode salvar sem código de barras
        errors = []
        errors += self.validate_partner_data(vals)
        if not payment_mode.one_time_payment:
            if not vals.get('barcode'):
                errors += ['Código de barras obrigatório']
            if len(vals['barcode']) != 44:
                errors += ['Código de barras deve possuir 44 dígitos - \
                           Verifique a linha digitável']
        return errors

    # Tributos com códigos de barras
    def validate_payment_type_04(self, payment_mode, vals):
        errors = []
        if not vals.get('barcode'):
            errors += ['Código de barras obrigatório']
        if len(vals['barcode']) != 44:
            errors += ['Código de barras deve possuir 44 dígitos - \
                       Verifique a linha digitável']
        return errors

    def validate_base_information(self, payment_mode):
        errors = []
        if not payment_mode.journal_id.company_id.cnpj_cpf:
            errors += ['Preencha o CNPJ da empresa']
        if not payment_mode.journal_id.company_id.legal_name:
            errors += ['Preencha a Razão Social da empresa']
        return errors

    def validate_information(self, payment_mode, vals):
        errors = []
        errors += self.validate_base_information(payment_mode)
        validate = getattr(
            self, 'validate_payment_type_%s' %
            payment_mode.payment_type, False)
        if validate:
            errors += validate(payment_mode, vals)
        if len(errors) > 0:
            msg = "\n".join(
                ["Por favor corrija os erros antes de prosseguir"] + errors)
            raise UserError(msg)

    @api.depends('payment_information_id')
    def _compute_final_value(self):
        for item in self:
            payment = item.payment_information_id
            desconto = payment.rebate_value + payment.discount_value
            acrescimo = payment.fine_value + payment.interest_value
            item.value_final = (item.amount_total - desconto + acrescimo)

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
            'fine_value': vals.get('fine_value'),
            'interest_value': vals.get('interest_value'),
            'numero_referencia': payment_mode_id.numero_referencia,
            'l10n_br_environment': payment_mode_id.l10n_br_environment
        }

    def action_generate_payment_order_line(self, payment_mode, vals):
        self.validate_information(payment_mode, vals)
        info_vals = self.get_information_vals(payment_mode, vals)
        information_id = self.env['l10n_br.payment_information'].sudo().create(
            info_vals)
        journal = payment_mode.journal_id
        line_vals = {
            'payment_mode_id': payment_mode.id,
            'journal_id': journal.id,
            'src_bank_account_id': journal.bank_account_id.id,
            'currency_id': payment_mode.journal_id.currency_id.id or
            payment_mode.journal_id.company_id.currency_id.id,
            'payment_information_id': information_id.id,
            'emission_date': date.today(),
            'type': 'payable',
            'nosso_numero': journal.l10n_br_sequence_nosso_numero.next_by_id(),
        }
        line_vals.update(vals)
        order_line = self.sudo().create(line_vals)
        move_line = self.env['account.move.line'].browse(vals['move_line_id'])
        move_line.write({'l10n_br_order_line_id': order_line.id})

    def action_aprove_payment_line(self):
        for item in self:
            if item.state != 'draft':
                raise UserError(
                    'Apenas pagamentos em provisório podem ser aprovados!')
            if item.type != 'payable':
                raise UserError(
                    'Apenas pagamentos a fornecedor podem ser aprovados')
            payment_order = self.get_payment_order(item.payment_mode_id)
            item.write({
                'payment_order_id': payment_order.id,
            })
        self.write({'state': 'approved'})

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

    def mark_order_line_processed(self, cnab_code, cnab_message,
                                  rejected=False, statement_id=None):
        state = 'processed'
        if rejected:
            state = 'rejected'

        self.write({
            'state': state, 'cnab_code': cnab_code,
            'cnab_message': cnab_message
        })
        if not statement_id:
            statement_id = self.env['l10n_br.payment.statement'].create({
                'name': '0001/Manual',
                'date': date.today(),
                'state': 'validated',
            })
        for item in self:
            self.env['l10n_br.payment.statement.line'].create({
                'statement_id': statement_id.id,
                'date': date.today(),
                'name': item.name,
                'partner_id': item.partner_id.id,
                'amount': item.value_final,
                'cnab_code': cnab_code,
                'cnab_message': cnab_message,
            })
        return statement_id

    def mark_order_line_paid(self, cnab_code, cnab_message, statement_id=None):
        bank_account_ids = self.mapped('src_bank_account_id')
        for account in bank_account_ids:
            order_lines = self.filtered(
                lambda x: x.src_bank_account_id == account)
            journal_id = self.env['account.journal'].search(
                [('bank_account_id', '=', account.id)], limit=1)

            if not statement_id:
                statement_id = self.env['l10n_br.payment.statement'].create({
                    'name':
                    journal_id.l10n_br_sequence_statements.next_by_id(),
                    'date': date.today(),
                    'state': 'validated',
                    'journal_id': journal_id.id,
                })
            for item in order_lines:
                move_id = self.create_move_and_reconcile(item)
                self.env['l10n_br.payment.statement.line'].create({
                    'statement_id': statement_id.id,
                    'date': date.today(),
                    'name': item.name,
                    'partner_id': item.partner_id.id,
                    'amount': item.value_final,
                    'move_id': move_id.id,
                    'cnab_code': cnab_code,
                    'cnab_message': cnab_message,
                })
            order_lines.write({'state': 'paid'})
        return statement_id

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
