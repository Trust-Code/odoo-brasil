# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import datetime
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models


class CashFlowReport(models.TransientModel):
    _name = 'account.cash.flow'
    _description = u'Cash Flow Report'

    @api.one
    def calc_final_amount(self):
        balance = 0
        for line in self.line_ids:
            balance += line.amount
        balance += self.start_amount
        self.final_amount = balance

    start_date = fields.Date(string="Start Date", required=True,
                             default=fields.date.today())
    end_date = fields.Date(
        string="End Date", required=True,
        default=fields.date.today()+datetime.timedelta(6*365/12))
    start_amount = fields.Float(string="Initial Value",
                                digits=dp.get_precision('Account'))
    final_amount = fields.Float(string="Total",
                                compute="calc_final_amount",
                                digits=dp.get_precision('Account'))
    line_ids = fields.One2many(
        "account.cash.flow.line", "cashflow_id",
        string="Cash Flow Lines")

    @api.model
    def json_list(self):
        dias = {}
        lista = []
        for item in self.line_ids:
            if item.date not in dias:
                dias[item.date] = len(lista)
                lista.append({'amount': item.amount, 'data': item.date,
                              'balance': item.balance})
            else:
                lista[dias[item.date]]['amount'] += item.amount
                if item.balance > lista[dias[item.date]]['amount']:
                    lista[dias[item.date]]['balance'] = item.balance
        return json.dumps(lista)

    @api.multi
    def calculate_liquidity(self):
        accs = self.env['account.account'].search(
            [('user_type_id.type', '=', 'liquidity')])
        liquidity_lines = []
        for acc in accs:
            continue
        return liquidity_lines

    @api.multi
    def calculate_moves(self):
        moveline_obj = self.env['account.move.line']
        moveline_ids = moveline_obj.search([
            '|',
            ('account_id.user_type_id.type', '=', 'receivable'),
            ('account_id.user_type_id.type', '=', 'payable'),
            ('reconciled', '=', False),
            ('move_id.state', '!=', 'draft'),
            ('company_id', '=', self.env.user.company_id.id),
            ('date_maturity', '<=', self.end_date),
        ])
        moves = []
        for move in moveline_ids:
            debit, credit = move.credit, move.debit
            amount = move.debit - move.credit

            moves.append({
                'name': move.ref or move.name,
                'cashflow_id': self.id,
                'partner_id': move.partner_id.id,
                'journal_id': move.journal_id.id,
                'account_id': move.account_id.id,
                'date': move.date_maturity,
                'debit': debit,
                'credit': credit,
                'amount': amount,
            })
        return moves

    @api.multi
    def action_calculate_report(self):
        self.write({'line_ids': [(5, 0, 0)]})
        balance = self.start_amount
        liquidity_lines = self.calculate_liquidity()
        move_lines = self.calculate_moves()

        move_lines.sort(key=lambda x: datetime.datetime.strptime(x['date'],
                                                                 '%Y-%m-%d'))

        for lines in liquidity_lines+move_lines:
            balance += lines['credit'] - lines['debit']
            lines['balance'] = balance
            self.env['account.cash.flow.line'].create(lines)


class CashFlowReportLine(models.TransientModel):
    _name = 'account.cash.flow.line'
    _description = u'Cash flow lines'

    name = fields.Char(string="Description", required=True)
    date = fields.Date(string="Date")
    partner_id = fields.Many2one("res.partner", string="Partner")
    account_id = fields.Many2one("account.account", string="Account")
    journal_id = fields.Many2one("account.journal", string="Journal")
    invoice_id = fields.Many2one("account.invoice", string="Invoice")
    debit = fields.Float(string="Debit",
                         digits=dp.get_precision('Account'))
    credit = fields.Float(string="Credit",
                          digits=dp.get_precision('Account'))
    amount = fields.Float(string="Balance(C-D)",
                          digits=dp.get_precision('Account'))
    balance = fields.Float(string="Accumulated Balance",
                           digits=dp.get_precision('Account'))
    cashflow_id = fields.Many2one("account.cash.flow", string="Cash Flow")
