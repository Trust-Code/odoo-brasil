# © 2019 Mackilem Van der Lann, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    preview_payment_ids = fields.One2many(
        string="Invoice Previews Payments",
        comodel_name="invoice.payment.lines",
        inverse_name="invoice_id",
        ondelete="set null")

    @api.onchange('preview_payment_ids')
    def _onchange_previews_balance(self):
        total = sum(self.preview_payment_ids.mapped('amount'))
        balance = self._get_amount() - total
        if balance != 0.0:
            amount = self.preview_payment_ids[-1].amount + balance
            self.preview_payment_ids[-1].amount = amount

    @api.onchange('payment_term_id')
    def _onchange_payment_term(self):
        self.preview_payment_ids = self.prepare_preview_payment()
        self._onchange_preview_payment_amount()

    def _get_amount(self):
        fields = ['icms_valor', 'ipi_valor', 'pis_valor', 'cofins_valor',
                  'issqn_valor', 'csll_valor', 'irrf_valor', 'inss_valor']
        total_retencao = 0
        for line in self.invoice_line_ids:
            for field in fields:
                if line[field] < 0:
                    total_retencao += line[field]
        return self.amount_total - abs(total_retencao)

    @api.onchange('invoice_line_ids')
    def _onchange_preview_payment_amount(self):
        balance = amount = self._get_amount()
        for line in self.preview_payment_ids:
            ptLine = line.payment_term_line_id or False
            if ptLine and ptLine.value == 'percent':
                mnt = round(amount * (ptLine.value_amount / 100), 2)
            elif ptLine and ptLine.value == 'fixed':
                mnt = ptLine.value_amount
            elif not ptLine or ptLine.value == 'balance':
                mnt = balance
            line.amount = mnt
            balance -= mnt

    def prepare_preview_payment(self, payment_term_id=False):
        pLine_env = self.env['invoice.payment.lines']
        pMode_env = self.env['l10n_br.payment.mode']
        pMode_default = pMode_env.search([('is_default', '=', True)], limit=1)
        result = []
        pTerm = payment_term_id if payment_term_id else self.payment_term_id
        if pTerm:
            for n, line in enumerate(pTerm.line_ids, 1):
                days = 0
                if line.option == 'day_after_invoice_date':
                    days = line.days
                dPreviews = pLine_env.get_date_previews(days)
                name = "%02d/%02d" % (n, len(pTerm.line_ids))
                vals = {'name': name,
                        'days': days,
                        'date_previews': dPreviews,
                        'payment_term_line_id': line.id}
                if line.default_payment_mode_id:
                    vals['payment_mode_id'] = line.default_payment_mode_id.id
                else:
                    vals['payment_mode_id'] = pMode_default.id
                result.append([0, 0, vals])
        else:
            dPreviews = pLine_env.get_date_previews()
            vals = {'name': '01/01',
                    'days': 0,
                    'date_previews': dPreviews,
                    'payment_mode_id': pMode_default.id}
            result.append([0, 0, vals])
        return result

    @api.multi
    def action_invoice_open(self):
        for s in self:
            if not s.preview_payment_ids:
                s._onchange_payment_term()
        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def finalize_invoice_move_lines(self, aml):
        aml = super(AccountInvoice, self).finalize_invoice_move_lines(aml)
        if self.account_id.user_type_id.type not in ['receivable', 'payable']:
            return aml
        # Filtra as contas para selecionar somente as de pagamento
        moves = [x for x in aml if x[2]['account_id'] == self.account_id.id]
        debit_credit = 'debit' if moves[0][2]['debit'] else 'credit'
        for move, payment in zip(moves, self.preview_payment_ids):
            move[2]['name'] = payment.name
            move[2]['date_maturity'] = payment.date_previews
            move[2][debit_credit] = payment.amount
            move[2]['payment_mode_id'] = payment.payment_mode_id.id
        return aml


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def create(self, vals):
        res = super(AccountInvoiceLine, self).create(vals)
        res.invoice_id._onchange_preview_payment_amount()
        return res
