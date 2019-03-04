# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class L10nBrPaymentStatement(models.Model):
    _name = 'l10n_br.payment.statement'

    _description = "Payment Statement"
    _order = "date desc, id desc"
    _inherit = ['mail.thread']

    @api.depends('journal_id')
    def _compute_currency(self):
        for item in self:
            item.currency_id = \
                item.journal_id.currency_id or item.company_id.currency_id

    @api.depends('line_ids.amount')
    def _compute_amount_total(self):
        for item in self:
            item.amount_total = sum([x.amount for x in item.line_ids])

    name = fields.Char(
        string='Reference',
        copy=False, readonly=True)
    type = fields.Selection([('receivable', 'Receivable'),
                             ('payable', 'Payable')], string="Type")
    date = fields.Date(
        copy=False, default=fields.Date.context_today)
    amount_total = fields.Monetary(
        'Valor Total',
        currency_field='currency_id', compute='_compute_amount_total')
    currency_id = fields.Many2one(
        'res.currency', compute='_compute_currency',
        string="Currency", store=True)
    journal_id = fields.Many2one(
        'account.journal', string='Journal', required=True)
    company_id = fields.Many2one(
        'res.company', related='journal_id.company_id', string='Company',
        store=True, readonly=True)

    line_ids = fields.One2many(
        'l10n_br.payment.statement.line', 'statement_id',
        string='Statement lines', readonly=True, copy=True)


class L10nBrPaymentStatementLine(models.Model):
    _name = 'l10n_br.payment.statement.line'
    _description = "Bank Statement Line"
    _order = "statement_id desc, date desc, id desc"

    name = fields.Char(string='Reference', required=True)
    nosso_numero = fields.Char(string="Nosso Número")
    date = fields.Date(string="Vencimento")
    effective_date = fields.Date(string="Data ocorrência")
    amount = fields.Monetary(
        digits=0, currency_field='journal_currency_id', string="Valor")
    journal_currency_id = fields.Many2one(
        'res.currency', related='statement_id.currency_id',
        help='Utility field to express amount currency', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    statement_id = fields.Many2one(
        'l10n_br.payment.statement', string='Statement',
        index=True, required=True, ondelete='cascade')
    journal_id = fields.Many2one(
        'account.journal', related='statement_id.journal_id',
        string='Journal', store=True, readonly=True)
    move_id = fields.Many2one('account.move', string="Lançamento")
    cnab_code = fields.Char(string="Código")
    cnab_message = fields.Char(string="Mensagem")
    company_id = fields.Many2one(
        'res.company', related='statement_id.company_id',
        string='Company', store=True, readonly=True)
    ignored = fields.Boolean(string="Ignorado?", default=False)
