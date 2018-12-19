# coding=utf-8
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class InvoiceEletronic(models.Model):
    _inherit = 'invoice.eletronic'

    @api.multi
    def validate_invoice(self):
        self.ensure_one()
        errors = self._hook_validation()
        errors1 = []
        if self.model == '65' and self.partner_id.cnpj_cpf is False:
            final_costumer = self.env['res.partner'].search(
                [('name', '=', 'Consumidor Final')]
            )
            if int(final_costumer) == int(self.partner_id.id):
                errors_remover = [
                    u'CNPJ/CPF do Parceiro inválido',
                    u'Destinatário - CNPJ/CPF'
                ]
                for erro in errors:
                    if erro not in errors_remover:
                        errors1.append(erro)
                errors = errors1

        if len(errors) > 0:
            msg = u"\n".join(
                [u"Por favor corrija os erros antes de prosseguir"] + errors)
            self.unlink()
            raise UserError(msg)

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        res = super(InvoiceEletronic, self)._prepare_eletronic_invoice_values()
        if self.model == '65':
            final_costumer = self.env['res.partner'].search(
                [('name', '=', 'Consumidor Final')]
            )
            if int(final_costumer) == int(self.partner_id.id):
                # Caso a prioridade seja outro modulo
                self.partner_id = False
                self.commercial_partner_id = False
                # Caso a prioridade esteja no modulo certo
                res['dest'] = None
        return res
