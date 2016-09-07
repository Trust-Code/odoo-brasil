# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel               #
# Copyright (C) 2012  Raphaël Valyi - Akretion                                #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from odoo import api, fields, models, _
from openerp.exceptions import except_orm
from openerp.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    amount_untaxed = fields.Float(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Untaxed Amount', store=True, help="The amount without tax")
    amount_tax = fields.Float(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Taxes', store=True, help="The tax amount")
    amount_total = fields.Float(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Total', store=True, help="The total amount")


    # TODO ask OpenERP SA for a _prepare_invoice method!
    def action_invoice_create(self, cr, uid, ids, *args):
        inv_id = super(PurchaseOrder, self).action_invoice_create(cr, uid,
                                                                   ids, *args)
        for order in self.browse(cr, uid, ids):
            # REMARK: super method is ugly as it assumes only one invoice
            # for possibly several purchase orders.
            if inv_id:
                company_id = order.company_id
                if not company_id.document_serie_product_ids:
                    raise except_orm(
                        _('No fiscal document serie found!'),
                        _("No fiscal document serie found for selected \
                        company %s") % (order.company_id.name))

                journal_id = order.fiscal_category_id and \
                order.fiscal_category_id.property_journal.id or False

                if not journal_id:
                    raise except_orm(
                        _(u'Nenhuma Diário!'),
                        _(u"Categoria de operação fisca: '%s', não tem um \
                        diário contábil para a empresa %s") % (
                            order.fiscal_category_id.name,
                            order.company_id.name))

                comment = ''
                if order.fiscal_position.inv_copy_note:
                    comment = order.fiscal_position.note or ''
                if order.notes:
                    comment += ' - ' + order.notes

                self.pool.get('account.invoice').write(cr, uid, inv_id, {
                     'fiscal_category_id': order.fiscal_category_id and
                     order.fiscal_category_id.id,
                     'fiscal_position': order.fiscal_position and
                     order.fiscal_position.id,
                     'issuer': '1',
                     'comment': comment,
                     'journal_id': journal_id})
        return inv_id



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', u'Posição Fiscal')



