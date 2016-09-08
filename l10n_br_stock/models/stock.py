# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# Copyright (C) 2012  Raphaël Valyi - Akretion                                #
# Copyright (C) 2014  Luis Felipe Miléo - KMEE - www.kmee.com.br              #
# Copyright (C) 2015  Michell Stuttgart - KMEE                                #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields, api


class StockIncoterms(models.Model):
    _inherit = 'stock.incoterms'

    freight_responsibility = fields.Selection(
        selection=[('0', u'Emitente'),
                   ('1', u'Destinatário'),
                   ('2', u'Terceiros'),
                   ('9', u'Sem Frete')],
        string=u'Frete por Conta',
        required=True,
        default='0')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _default_fiscal_category(self):
        user = self.env['res.users'].browse(self._uid).with_context(
            dict(self._context))
        return user.company_id.stock_fiscal_category_id 

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string=u'Posição Fiscal',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    ind_pres = fields.Selection(
        selection=[('0', u'Não se aplica'),
                   ('1', u'Operação presencial'),
                   ('2', u'Operação não presencial, pela Internet'),
                   ('3', u'Operação não presencial, Teleatendimento'),
                   ('4', u'NFC-e em operação com entrega em domicílio'),
                   ('9', u'Operação não presencial, outros'),],
        string=u'Tipo de operação',
        default='0',
        help=u'Indicador de presença do comprador no estabelecimento '
             u'comercial no momento da operação.')


    @api.multi
    def onchange_company_id(self, partner_id, company_id=False,
                            fiscal_category_id=False):
        context = dict(self._context)
        result = {'value': {'fiscal_position': False}}

        if not partner_id or not company_id:
            return result

        partner = self.env['res.partner'].browse(partner_id)
        partner_address = partner.address_get(['invoice', 'delivery'])

        partner_invoice_id = partner_address['invoice']
        partner_shipping_id = partner_address['delivery']

        kwargs = {
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'partner_shipping_id': partner_shipping_id,
            'company_id': company_id,
            'context': context,
        }
        return self._fiscal_position_map(result, **kwargs)


class StockMove(models.Model):

    _inherit = "stock.move"

    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal Position',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    @api.model
    @api.returns
    def _fiscal_position_map(self, result, **kwargs):
        kwargs['context'].update({'use_domain': ('use_picking', '=', True)})
        fp_rule_obj = self.env['account.fiscal.position.rule']
        return fp_rule_obj.apply_fiscal_mapping(result, **kwargs)


    @api.onchange('product_id')
    def _onchange_product_id(self):
        context = self._context
        
        parent_fiscal_category_id = context.get('parent_fiscal_category_id')
        picking_type = context.get('picking_type')
        if context.get('company_id', False):
            company_id = context['company_id']
        else:
            company_id = self.env['res.users'].browse(
                self._uid).with_context(context).company_id.id

        result = {'value': {}}

        if parent_fiscal_category_id and product_id and picking_type:

            obj_fp_rule = self.env['account.fiscal.position.rule']
            product_fc_id = obj_fp_rule.product_fiscal_category_map(
                self._cr, self._uid, product_id, parent_fiscal_category_id)

            if product_fc_id:
                parent_fiscal_category_id = product_fc_id

            result['value']['fiscal_category_id'] = parent_fiscal_category_id

            partner = self.env['res.partner'].browse(partner_id)
            partner_address = partner.address_get(['invoice', 'delivery'])

            partner_invoice_id = partner_address['invoice']
            partner_shipping_id = partner_address['delivery']

            kwargs = {
                'partner_id': partner_id,
                'partner_invoice_id': partner_invoice_id,
                'partner_shipping_id': partner_shipping_id,
                'company_id': company_id,
                'context': context
            }

            result.update(self._fiscal_position_map(result, **kwargs))

        if 'value' in result_super:
            result_super['value'].update(result['value'])

        return result_super

