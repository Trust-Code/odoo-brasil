# © 2018 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from itertools import product
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def group_invoices(self, group_dict):
        """
        group_dict = [{"rule_name": 'serv_01.05', "fpos": 1,
                       "domain": [('service_type_id', '=', 7)]},
                      ]
        """
        vals = self._prepare_invoice_dict(group_dict)
        for inv in vals:
            self._create_invoices_grouped(inv)

    @api.multi
    def _prepare_invoice_dict(self, group_dict):
        """
        Primeiro pega todas as notas possíveis de agrupar e depois
        separa conforme regras específicadas
        """
        vals = []
        if self.ids:
            inv = self.filtered(lambda l: l.state == "draft")
        else:
            today = datetime.today()
            inv = self.search(
                [('state', '=', 'draft'),
                 '|', '&',
                 ('date_invoice', '>=', today + relativedelta(day=1)),
                 ('date_invoice', '<=', today + relativedelta(day=31)),
                 ('date_invoice', '=', False)])
        lines = inv.mapped('invoice_line_ids')
        inv_grouped = []

        for group in group_dict:
            if 'domain' not in group:
                continue
            group['domain'].append(('id', 'in', lines.ids))
            group_lines = lines.search(group['domain'])
            for v in self._prepare_vals(group_lines):
                # Split when there is one invoice and more then one rule
                if len(v['inv_ids']) <= 1:
                    inv_lines = v['inv_ids'].invoice_line_ids.ids
                    if len(inv_lines) == len(v['lines']):
                        continue
                v['rule'] = group['rule_name']
                v['fpos'] = group['fpos'] if 'fpos' in group else False
                vals.append(v)
                [inv_grouped.append(id) for id in v['inv_ids'].ids]
                lines -= group_lines
        # Remainig lines
        for inv in lines.mapped('invoice_id'):
            if inv.id in inv_grouped:
                ln_remainig = lines.filtered(lambda x: x.invoice_id == inv)
                rv = self._prepare_vals(ln_remainig)
                rv[0]['rule'] = _('Reallocated by the grouping rule')
                rv[0]['fpos'] = inv.fiscal_position_id.id or False
                vals.append(rv[0])
        return vals

    def _prepare_vals(self, lines):
        inv_vals = []
        comp_ids = lines.mapped('company_id')
        part_ids = lines.mapped('partner_id')
        for (company, partner) in product(comp_ids, part_ids):
            ln = lines.filtered(lambda l: l.company_id == company
                                and l.partner_id == partner)
            inv_ids = ln.mapped('invoice_id')
            if ln:
                inv_vals.append({'company': company,
                                 'partner': partner,
                                 'lines': ln,
                                 'inv_ids': inv_ids})
                lines -= ln
            if not lines:
                break
        return inv_vals

    def _create_invoices_grouped(self, inv):
        fpos_id, journal_id = self._get_fpos_journal(inv)
        partner_id = inv['partner']
        company = inv['company']
        inv_ids = inv['inv_ids']
        origin = ''
        for org in inv_ids.filtered('origin').mapped('origin'):
            origin += "%s, " % org
        pgto_ids = inv_ids.mapped('payment_term_id')
        mode_ids = inv_ids.mapped('payment_mode_id')
        user_ids = inv_ids.mapped('user_id')
        team_ids = inv_ids.mapped('team_id')
        obs_ids = fpos_id.fiscal_observation_ids.ids
        [i.action_invoice_cancel_paid() for i in inv_ids if i.state == "draft"]
        gr_invoice_id = self.create({
            'origin': origin or '',
            'type': 'out_invoice',
            'account_id': partner_id.with_context(
                force_company=company.id).property_account_receivable_id.id,
            'partner_id': partner_id.id,
            'partner_shipping_id': partner_id.id,
            'journal_id': journal_id.id,
            'currency_id': company.currency_id.id,
            'payment_term_id': pgto_ids[0].id if pgto_ids else False,
            'payment_mode_id': mode_ids[0].id if mode_ids else False,
            'fiscal_position_id': fpos_id.id,
            'service_document_id': fpos_id.service_document_id.id,
            'service_serie_id': fpos_id.service_serie_id.id,
            'fiscal_observation_ids': [(6, 0, obs_ids)],
            'company_id': company.id,
            'user_id': user_ids[0].id if user_ids else False,
            'team_id': team_ids[0].id if team_ids else False
        })
        for line in inv['lines']:
            vals = {
                'invoice_id': gr_invoice_id.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'name': line.name,
                'sequence': line.sequence,
                'origin': line.origin,
                'account_id': line.account_id.id,
                'invoice_line_tax_ids': [
                    (6, 0, [tax.id for tax in line.invoice_line_tax_ids])]
                }
            new_line = self.env['account.invoice.line'].create(vals)
            new_line._br_account_onchange_product_id()
            new_line._set_taxes_from_fiscal_pos()
        gr_invoice_id._onchange_invoice_line_ids()

        cancel_msg = ("""
            <p>This invoice was canceled by group rule named %s and
                created the invoice:
                <a href='#' data-oe-model='account.invoice'
                            data-oe-id='%s'> %s
                </a>
            </p>""" % (inv['rule'], gr_invoice_id.id, partner_id.name))

        [i.message_post(cancel_msg) for i in inv_ids]
        msg_ids = ''
        for id in inv_ids.ids:
            msg_ids += """<a href='#' data-oe-model='account.invoice'
                                     data-oe-id='%s'> inv_%s -
                          </a>""" % (id, id)

        new_msg = ("""
            <p>This invoice was created by group rule named %s and
                grouped this invoices: %s
            </p>""" % (inv['rule'], msg_ids))
        gr_invoice_id.message_post(body=new_msg)
        return gr_invoice_id

    def _get_fpos_journal(self, inv):
        aj = self.env['account.journal']
        afp = self.env['account.fiscal.position']
        company = inv['company']
        fpos_id = journal_id = False

        if 'fpos' in inv and inv['fpos']:
            fpos_id = afp.browse(inv['fpos'])
        else:
            fpos_id = inv['partner'].with_context(
                force_company=company.id).property_account_position_id
        if fpos_id:
            journal_id = fpos_id.journal_id or False
        if not journal_id:
            domain = [('company_id', '=', company.id), ('type', '=', 'sale')]
            journal_id = aj.search(domain, limit=1)

        return fpos_id, journal_id
