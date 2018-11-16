# -*- coding: utf-8 -*-
# Fábio Luna - NDS Sistemas

from odoo import fields, models, api
from datetime import date


class MulticompanyPayment(models.TransientModel):
    _name = 'multicompany.payment'

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
    )
    account_id = fields.Char(string="Account")
    payment_value = fields.Float(string="Payment Value")
    amount_residual = fields.Float(string="Amount Residual")
    date_maturity = fields.Date(string="Date Maturity")
    move_line_id = fields.Integer(string="Move Id")
    move_name = fields.Char(string="Move Name")
    reconciled = fields.Boolean(string="Reconciled")

    def get_moves(self, partner_id):
        move_ids = self.sudo().env['account.move.line'].search([
            ('partner_id', '=', partner_id.id),
            ('invoice_id', '!=', None),
            ('payment_value', '>', 0),
            ('reconciled', '=', False)
        ])

        for move in move_ids:
            account_id = move.account_id.code + ' ' + move.account_id.name
            vals = {
                'partner_id': partner_id.id,
                'account_id': account_id,
                'payment_value': move.payment_value,
                'amount_residual': move.amount_residual,
                'date_maturity': move.date_maturity,
                'move_line_id': move.id,
                'move_name': move.move_id.name,
                'reconciled': move.reconciled,
            }

            self += self.create(vals)

        return self

    def create_multi_company_moves(self, line):
        # Primeira parte gera o movimento para a empresa do modo de pagamento
        # Não precisa conciliar esse movimento
        journal_company = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.user.company_id.id)], limit=1)
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': journal_company.id,
            'company_id': journal_company.company_id.id,
            'date': date.today(),
            'ref': line.name,
        })
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        counterpart_aml_dict = {
            'name': line.name,
            'move_id': move.id,
            'partner_id': line.partner_id.id,
            'debit': 0.0,
            'credit': line.payment_value,
            'currency_id': line.currency_id.id,
            'account_id': 978,
        }
        liquidity_aml_dict = {
            'name': line.name,
            'move_id': move.id,
            'partner_id': line.partner_id.id,
            'debit': line.payment_value,
            'credit': 0.0,
            'currency_id': line.currency_id.id,
            'account_id': journal_company.default_debit_account_id.id,
        }
        aml_obj.create(counterpart_aml_dict)
        aml_obj.create(liquidity_aml_dict)
        move.post()

        # Lançamento de equilíbrio
        journal_company = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', line.move_id.company_id.id)], limit=1)
        move = self.env['account.move'].create({
            'name': '/',
            'journal_id': journal_company.id,
            'company_id': journal_company.company_id.id,
            'date': date.today(),
            'ref': line.name,
        })
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        counterpart_aml_dict = {
            'name': line.name,
            'move_id': move.id,
            'partner_id': line.partner_id.id,
            'debit': line.payment_value,
            'credit': 0.0,
            'currency_id': line.currency_id.id,
            'account_id': 979,
        }
        liquidity_aml_dict = {
            'name': line.name,
            'move_id': move.id,
            'partner_id': line.partner_id.id,
            'debit': 0.0,
            'credit': line.payment_value,
            'currency_id': line.currency_id.id,
            'account_id': journal_company.default_credit_account_id.id,
        }
        aml_obj.create(counterpart_aml_dict)
        aml_obj.create(liquidity_aml_dict)
        move.post()

        # Segunda parte cria-se o movimento na filial
        # Esse movimento deve ser conciliado
        journal_filial = self.env['account.journal'].search(
            [('type', '=', 'bank'),
             ('company_id', '=', line.move_id.company_id.id)], limit=1)
        move_filial = self.env['account.move'].create({
            'name': '/',
            'journal_id': journal_filial.id,
            'company_id': journal_filial.company_id.id,
            'date': date.today(),
            'ref': line.name,
        })
        counterpart_aml_dict = {
            'name': line.name,
            'move_id': move_filial.id,
            'partner_id': line.partner_id.id,
            'debit': 0.0,
            'credit': line.payment_value,
            'currency_id': line.currency_id.id,
            'account_id': line.account_id.id,
        }
        liquidity_aml_dict = {
            'name': line.name,
            'move_id': move_filial.id,
            'partner_id': line.partner_id.id,
            'debit': line.payment_value,
            'credit': 0.0,
            'currency_id': line.currency_id.id,
            'account_id': journal_filial.default_debit_account_id.id,
        }
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False, default_journal_id=journal_filial.id)
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        aml_obj.create(liquidity_aml_dict)
        move_filial.post()
        (counterpart_aml + line).reconcile()
        return move

    @api.multi
    def action_register_payment(self):
        for move in self:
            move_line_id = self.env['account.move.line'].browse(
                move.move_line_id)

            self.create_multi_company_moves(move_line_id)
