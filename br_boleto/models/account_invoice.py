# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    boleto = fields.Boolean(related="payment_mode_id.boleto")

    def _get_email_template_invoice(self):
        return self.env.user.company_id.boleto_email_tmpl

    @api.multi
    def send_email_boleto_queue(self):
        mail = self._get_email_template_invoice()
        if not mail:
            raise UserError(_('Modelo de email padrão não configurado'))

        attachment_obj = self.env['ir.attachment']
        for item in self:

            atts = []
            self = self.with_context({
                'origin_model': 'account.invoice',
                'active_ids': [item.id],
            })

            attachment_obj = self.env['ir.attachment']
            boleto_report = self.env['ir.actions.report'].search(
                [('report_name', '=',
                  'br_boleto.report.print')])
            report_service = boleto_report.xml_id
            boleto, dummy = self.env.ref(report_service).render_qweb_pdf(
                [item.id])

            if boleto:
                name = "boleto-%s-%s.pdf" % (
                    item.number, item.partner_id.commercial_partner_id.name)
                boleto_id = attachment_obj.create(dict(
                    name=name,
                    datas_fname=name,
                    datas=base64.b64encode(boleto),
                    mimetype='application/pdf',
                    res_model='account.invoice',
                    res_id=item.id,
                ))
                atts.append(boleto_id.id)

            values = {
                "attachment_ids": atts + mail.attachment_ids.ids
            }
            mail.send_mail(item.id, email_values=values)

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        error = ''
        for item in self:
            if not item.payment_mode_id:
                continue
            if item.payment_mode_id.type != 'receivable':
                continue
            if not item.payment_mode_id.boleto:
                continue
            if not item.company_id.partner_id.legal_name:
                error += u'Empresa - Razão Social\n'
            if not item.company_id.cnpj_cpf:
                error += u'Empresa - CNPJ\n'
            if not item.company_id.district:
                error += u'Empresa - Bairro\n'
            if not item.company_id.zip:
                error += u'Empresa - CEP\n'
            if not item.company_id.city_id.name:
                error += u'Empresa - Cidade\n'
            if not item.company_id.street:
                error += u'Empresa - Logradouro\n'
            if not item.company_id.number:
                error += u'Empresa - Número\n'
            if not item.company_id.state_id.code:
                error += u'Empresa - Estado\n'

            if not item.commercial_partner_id.name:
                error += u'Cliente - Nome\n'
            if item.commercial_partner_id.is_company and \
               not item.commercial_partner_id.legal_name:
                error += u'Cliente - Razão Social\n'
            if not item.commercial_partner_id.cnpj_cpf:
                error += u'Cliente - CNPJ/CPF \n'
            if not item.commercial_partner_id.district:
                error += u'Cliente - Bairro\n'
            if not item.commercial_partner_id.zip:
                error += u'Cliente - CEP\n'
            if not item.commercial_partner_id.city_id.name:
                error += u'Cliente - Cidade\n'
            if not item.commercial_partner_id.street:
                error += u'Cliente - Logradouro\n'
            if not item.commercial_partner_id.number:
                error += u'Cliente - Número\n'
            if not item.commercial_partner_id.state_id.code:
                error += u'Cliente - Estado\n'

            if item.number and len(item.number) > 12:
                error += u'Numeração da fatura deve ser menor que 12 ' + \
                    'caracteres quando usado boleto\n'

            if len(error) > 0:
                raise UserError(_("""Ação Bloqueada!
Para prosseguir é necessário preencher os seguintes campos:\n""") + error)
        return res

    @api.multi
    def action_print_boleto(self):
        if self.state in ('draft', 'cancel'):
            raise UserError(
                _('Fatura provisória ou cancelada não permite emitir boleto'))
        self = self.with_context({'origin_model': 'account.invoice'})
        return self.env.ref(
            'br_boleto.action_boleto_account_invoice').report_action(self)
