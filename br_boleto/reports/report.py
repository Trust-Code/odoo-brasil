# -*- coding: utf-8 -*-
# © 2012-2015 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models
from odoo.exceptions import UserError
from ..boleto.document import Boleto


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def render_qweb_html(self, res_ids, data=None):
        if self.name == 'Boleto':
            return
        return super(IrActionsReport, self).render_qweb_html(
            res_ids, data=data)

    def render_qweb_pdf(self, res_ids, data=None):
        if not self.name == 'Boleto':
            return super(IrActionsReport, self).render_qweb_pdf(
                res_ids, data=data)

        move_line_ids = self.env['account.move.line'].browse()
        if self.model == 'account.invoice':
            ai_obj = self.env['account.invoice']
            for account_invoice in ai_obj.browse(res_ids):
                for move_line in account_invoice.receivable_move_line_ids:
                    move_line_ids |= move_line
        elif self.model == 'account.move.line':
            move_line_ids = self.env['account.move.line'].browse(res_ids)
        else:
            raise UserError(u'Parâmetros inválidos')
        move_line_ids = move_line_ids.filtered(
            lambda x: x.payment_mode_id.boleto)
        order_line_ids = self.env['payment.order.line'].action_register_boleto(
            move_line_ids)
        boleto_list = order_line_ids.generate_boleto_list()
        if not boleto_list:
            if self.env.context.get('ignore_empty_boleto'):
                return None, 'pdf'
            raise UserError('Nenhum boleto a ser emitido!')
        pdf_string = Boleto.get_pdfs(boleto_list)
        return pdf_string, 'pdf'
