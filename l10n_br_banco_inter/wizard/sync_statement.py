from odoo import models, fields


class WizardSyncStatement(models.TransientModel):
    _name = 'wizard.sync.statement'
    _description = "Wizard Sincronizacao Extrato"

    journal_id = fields.Many2one('account.journal', string="Journal", required=True)
    start_date = fields.Date(string="Data Inicio", required=True)
    end_date = fields.Date(string="Data Final", required=True)

    def action_sync_statement(self):
        return self.journal_id.sync_bank_statement_online_inter(self.start_date, self.end_date)
