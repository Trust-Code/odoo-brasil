# © 2017 Mackilem Van der Laan, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from itertools import product


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
        if vals:
            for inv in vals:
                self._create_invoices_grouped(inv)

    @api.multi
    def _prepare_invoice_dict(self, group_dict):
        vals = []
        if self.ids:
            inv = self.filtered(lambda l: l.state == "draft")
        else:
            inv = self.search([('state', '=', 'draft')])
        lines = inv.mapped('invoice_line_ids')

        for group in group_dict:
            if 'domain' not in group and not group['domain']:
                continue
            group['domain'].append(('id', 'in', lines.ids))
            f_lines = lines.search(group['domain'])
            for v in self._prepare_vals(f_lines):
                v['rule'] = group['rule_name']
                v['fpos'] = group['fpos'] or False
                vals.append(v)
            lines -= f_lines

        return vals

    def _prepare_vals(self, lines):
        inv_vals = []
        comp_ids = lines.mapped('company_id')
        part_ids = lines.mapped('partner_id')
        for (c, p) in product(comp_ids, part_ids):
            ln = lines.filtered(lambda l: l.company_id == c
                                and l.partner_id == p)
            if ln:
                inv_vals.append({'company': c, 'partner': p, 'lines': ln})
                lines -= ln
            if not lines:
                break
        return inv_vals

    def _create_invoices_grouped(self, inv):
        fpos_id, journal_id = self._get_fpos_journal(inv)
        partner_id = inv['partner']
        company = inv['company']
        inv_ids = inv['lines'].mapped('invoice_id')
        origin = [org for org in inv_ids.mapped('origin') if org]
        pgto_ids = inv_ids.mapped('payment_term_id')
        user_ids = inv_ids.mapped('user_id')
        team_ids = inv_ids.mapped('team_id')

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
            'fiscal_position_id': fpos_id.id,
            'company_id': company.id,
            'user_id': user_ids[0].id if user_ids else False,
            'team_id': team_ids[0].id if team_ids else False
        })
        for line in inv['lines']:
            line.copy({'invoice_id': gr_invoice_id.id})

        cancel_msg = ("""
            <p>This invoice was canceled by group rule named %s and
                created the invoice:
                <a href='#' data-oe-model='account.invoice'
                            data-oe-id='%s'> %s
                </a>
            </p>""" % (inv['rule'], gr_invoice_id.id, partner_id.name))

        [i.message_post(cancel_msg) for i in inv_ids]
        [i.action_invoice_cancel_paid() for i in inv_ids if i.state == "draft"]
        msg_ids = ''
        for id in inv_ids.ids:
            msg_ids += """<a href='#' data-oe-model='account.invoice'
                                     data-oe-id='%s'> inv_%s -
                          </a>""" % (id, id)

        new_msg = ("""
            <p>This invoice was created by group rule named %s and
                grouped this invoices: %s
            </p>""" % (inv['rule'], msg_ids))
        gr_invoice_id.message_post(new_msg)

    def _get_fpos_journal(self, inv):
        aj = self.env['account.journal']
        afp = self.env['account.fiscal.position']
        company = inv['company']
        fpos_id = journal_id = False

        if 'fpos' in inv:
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
