# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from odoo import api, fields, models
from odoo.exceptions import UserError

STATE = {'draft': [('readonly', False)]}


class L10nBrScheduledTransfer(models.Model):
    _name = 'l10n_br.scheduled.transfer'
    _description = 'Schedule automatic transfer via CNAB'
    _order = 'id desc'

    name = fields.Char(string="Nome", readonly=True, states=STATE)
    notes = fields.Char(string="Notas", readonly=True, states=STATE)

    destiny_journal_id = fields.Many2one(
        'account.journal', string="Banco Destino", required=True,
        readonly=True, states=STATE)

    payment_mode_id = fields.Many2one(
        'l10n_br.payment.mode', string="Modo de Pagamento", required=True,
        readonly=True, states=STATE)

    company_id = fields.Many2one(
        'res.company', string="Empresa", readonly=True, states=STATE,
        default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(
        'res.currency', string="Moeda",
        related="company_id.currency_id", readonly=True)
    amount = fields.Monetary(string="Valor a Transferir", required=True,
                             readonly=True, states=STATE)
    transfer_date = fields.Date(
        string="Data de Transferência", readonly=True, states=STATE)
    state = fields.Selection(
        [('draft', 'Provisório'), ('scheduled', 'Agendado'),
         ('done', 'Finalizado'), ('cancelled', 'Cancelado')],
        string="Situação", default="draft", readonly=True)

    payment_line_id = fields.Many2one(
        'payment.order.line', "Pagamento agendado", readonly=True)

    @api.multi
    def _validate_transfer(self):
        for item in self:
            if item.payment_mode_id.journal_id == item.destiny_journal_id:
                raise UserError(
                    'As conta de destino não pode ser a mesma do modo \
                    de pagamento!')
            if item.amount <= 0.0:
                raise UserError('O valor a transferir deve ser positivo!')
            transfer_date = fields.Date.from_string(item.transfer_date)
            if transfer_date < date.today():
                raise UserError(
                    'Data de transferência deve ser maior ou igual a hoje!')

    def _prepare_values(self):
        bank_account = self.destiny_journal_id.bank_account_id
        return {
            'partner_id': self.company_id.partner_id.id,
            'amount_total': self.amount,
            'name': self.name,
            'partner_ref': self.notes,
            'destiny_journal_id': self.destiny_journal_id.id,
            "bank_account_id": bank_account.id,
            'partner_acc_number': bank_account.acc_number,
            'partner_bra_number': bank_account.bra_number,
            'date_maturity': self.transfer_date,
        }

    def _get_next_code(self):
        sequence_id = self.env['ir.sequence'].sudo().search(
            [('code', '=', 'l10n_br_.bank.transfer'),
             ('company_id', '=', self.company_id.id)])
        if not sequence_id:
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': 'Sequencia de Transferencia Bancária',
                'code': 'l10n_br_.bank.transfer',
                'company_id': self.company_id.id,
                'prefix': 'TRANSFER/%(year)s/',
                'padding': 4,
            })

        return sequence_id.next_by_id()

    @api.multi
    def action_schedule_transfer(self):
        self._validate_transfer()
        line_obj = self.env['payment.order.line']
        for item in self:
            item.write({'name': item._get_next_code()})
            vals = item._prepare_values()
            order_line = line_obj.action_generate_payment_order_line(
                item.payment_mode_id, vals)
            item.write({'payment_line_id': order_line.id})

        self.write({'state': 'scheduled'})

    @api.multi
    def action_cancel(self):
        for item in self:
            if item.payment_line_id.state == 'draft':
                item.payment_line_id.unlink()
            elif item.payment_line_id.state in ('rejected', 'cancelled'):
                item.payment_line_id = False
            else:
                raise UserError('Existe uma ordem de pagamento vinculada!')
        self.write({'state': 'cancelled'})

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})

    @api.multi
    def action_set_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise UserError('Apenas transferências no estado provisório \
                                podem ser excluidas')
        return super(L10nBrScheduledTransfer, self).unlink()
