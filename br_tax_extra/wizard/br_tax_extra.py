import math
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp

from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CSOSN_SIMPLES

class BrTaxExtra(models.TransientModel):

    _name = 'br.tax.extra'

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    release_type = fields.Selection([('in', u'Entrada'), ('out', u'Saída')], string=u'Tipo de Lançamento', default='in')
    purchase_orders = fields.Many2many('purchase.order', 'br_tax_extra_po_rel', 'tax_extra_id', 'purchase_order_id',
                                       string=u'Pedidos de Compra Relacionados')
    create_voucher = fields.Boolean(string=u'Lançar Contas à Pagar', default=False)
    partner_id = fields.Many2one('res.partner', string=u'Parceiro')
    journal_id = fields.Many2one('account.journal', string='Diário')
    extra_tax_lines = fields.Many2many('br.tax.extra.line', 'tax_extra_id', string='Produtos')
    cost_type = fields.Selection([('tax', u'Imposto'), ('freight', u'Frete')])
    total_icmsst_frete_manual = fields.Monetary(string=u'Total ICMS ST - Frete', digits=dp.get_precision('Account'))

    @api.onchange('total_icmsst_frete_manual')
    def average_icmsst_frete(self):
        icmsst_frete = self.total_icmsst_frete_manual
        product_values_total = 0
        max_value_product = 0
        icms_st_frete_valor_manual_sum = 0
        for product in self.extra_tax_lines:
            product_values_total += product.product_po_value
            if product.product_po_value > max_value_product:
                max_value_product = product.product_po_value
        avg_icmsst_frete = icmsst_frete / product_values_total if icmsst_frete > 0 else 0
        for product in self.extra_tax_lines:
            product.icms_st_frete_valor_manual = round(avg_icmsst_frete * product.product_po_value,
                                                       2) if icmsst_frete > 0 else 0
            icms_st_frete_valor_manual_sum += product.icms_st_frete_valor_manual
            product.compute_cost_extra()
        # Hook para Corrigir Arredondamento
        if icms_st_frete_valor_manual_sum != icmsst_frete:
            for product in self.extra_tax_lines:
                if product.product_po_value == max_value_product:
                    product.icms_st_frete_valor_manual += (icmsst_frete - icms_st_frete_valor_manual_sum)
                    product.compute_cost_extra()
                    continue

    @api.multi
    @api.onchange('purchase_orders')
    def search_values_in_orders(self):
        #TODO: se o pedido ainda não estiver como recebido, retornar um alerta e não carregar os produtos
        lines = []
        products_not_received = []
        for po in self.purchase_orders:
            for line in po.order_line:
                if line.product_qty != line.qty_received:
                    products_not_received.append(" - O Produto %s não foi completamente recebido,"
                            "aguarde o recebimento integral do produto para adicionar custos extras.\n" \
                            % line.product_id.name)

                new_line = {
                    'product_id': line.product_id.id,
                    'company_id': line.company_id.id,
                    'po_id': po.id,
                    'product_qty': line.product_qty,
                    'product_po_value': line.price_total,
                    'product_po_unit_cost': line.price_unit,
                    'qty_received': line.qty_received,
                }

                lines.append(self.env['br.tax.extra.line'].create(new_line).id)

        if len(products_not_received) > 0:
            errors = ''
            for error in products_not_received:
                errors += error
            raise ValidationError(_(errors))

        self.extra_tax_lines = self.env['br.tax.extra.line'].browse(lines)

    @api.multi
    def compute_extra_cost(self):
        lines = []
        AccountMove = self.env['account.move']
        for product in self.extra_tax_lines:
            debit, credit, journal_id = product.do_change_standard_price()
            lines.append(debit)
            lines.append(credit)

        move_vals = {
            'journal_id': journal_id,
            'company_id': product.company_id.id,
            'line_ids': lines,
        }
        move = AccountMove.create(move_vals)
        move.post()
        voucher = self.create_voucher_extra_taxes()

        return voucher

    @api.multi
    def create_voucher_extra_taxes(self):
        voucher_obj = self.env['account.voucher']

        for record in self:
            values = {
                'partner_id': record.partner_id.id,
                'account_id':
                    record.partner_id.property_account_payable_id.id,
                'date': fields.Date.today(),
                'pay_now': 'pay_later',
                'voucher_type': 'purchase',
                'journal_id': record.journal_id.id,
                'reference': u'Impostos Cobrados na Entrada',
            }

            line_vals = []
            icms_st_vlr = 0
            icms_st_frete_vlr = 0

            for line in record.extra_tax_lines:
                icms_st_vlr += line.icms_st_valor_manual
                icms_st_frete_vlr += line.icms_st_frete_valor_manual

            if icms_st_vlr > 0:
                line_icms_st = {
                    'quantity': 1,
                    'name': u'ICMS ST - Entrada',
                    'price_unit': icms_st_vlr,
                    'account_id': record.journal_id.default_debit_account_id.id,
                    'company_id': record.company_id.id,
                }

                line_vals.append((0, 0, line_icms_st))

            if icms_st_frete_vlr > 0:
                line_icms_st_frete = {
                    'quantity': 1,
                    'name': u'ICMS ST Frete - Entrada',
                    'price_unit': icms_st_frete_vlr,
                    'account_id': record.journal_id.default_debit_account_id.id,
                    'company_id': record.company_id.id,
                }

                line_vals.append((0, 0, line_icms_st_frete))

        values['line_ids'] = line_vals

        voucher_id = voucher_obj.create(values)

        return voucher_id

class BrTaxExtraLine(models.TransientModel):

    _name = 'br.tax.extra.line'

    def should_round_down(self, val):
        if val < 0:
            return ((val * -1) % 1) < 0.5
        return (val % 1) < 0.5

    def round_value(self, val, ndigits=0):
        if ndigits > 0:
            val *= 10 ** (ndigits - 1)

        is_positive = val > 0
        tmp_val = val
        if not is_positive:
            tmp_val *= -1

        rounded_value = math.floor(tmp_val) if self.should_round_down(val) else math.ceil(tmp_val)
        if not is_positive:
            rounded_value *= -1

        if ndigits > 0:
            rounded_value /= 10 ** (ndigits - 1)

        return rounded_value

    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.user.company_id.id)
    po_id = fields.Many2one('purchase.order', string=u'Pedido de Compra')
    tax_ids = fields.Many2many('account.fiscal.position.tax.rule', string=u'Regra Imposto')
    product_id = fields.Many2one('product.product', u'Produto')
    product_qty = fields.Float(string='Qtd', required=True)
    product_po_value = fields.Monetary(string=u'Vlr Prod (Pedido)', store=True)
    product_po_unit_cost = fields.Monetary(string=u'Vlr Unit (Pedido)', store=True)
    product_extra_cost = fields.Monetary(string=u'Custo Extra', store=True)
    product_total_cost = fields.Monetary(string=u'Vlr Final', store=True)
    qty_received = fields.Float(string=u'Qtd. Recebida')

    # Dados de Impostos
    product_mva = fields.Float(string=u'MVA')

    # Dados ICMS ST
    icms_st_cst = fields.Selection(CST_ICMS + CSOSN_SIMPLES, string=u'Situação Tributária', readonly=True)
    icms_st_aliquota = fields.Float(string=u'Alíquota ( % )', digits=dp.get_precision('Account'), readonly=True)
    icms_st_base_calculo = fields.Monetary(string=u'Base de Cálculo', digits=dp.get_precision('Account'),
                                           compute='compute_tax', readonly=True)
    icms_st_aliquota_reducao_base = fields.Float(string=u'Redução Base ( % )', digits=dp.get_precision('Account'),
                                              readonly=True)
    icms_st_valor = fields.Monetary(string=u'Valor ICMS ST', digits=dp.get_precision('Account'), compute='compute_tax',
                                    readonly=True)
    icms_valor_manual = fields.Monetary(string=u'Vlr ICMS', digits=dp.get_precision('Account'))
    icms_st_valor_manual = fields.Monetary(string=u'Vlr ICMS ST', digits=dp.get_precision('Account'))
    icms_st_frete_valor_manual = fields.Monetary(string=u'Vlr ICMS ST - Frete', digits=dp.get_precision('Account'))

    @api.multi
    def compute_icms_st(self, price_base, mva, base_reduction=0):
        base_icmsst = price_base
        reducao_icmsst = base_reduction
        aliquota_mva = mva

        base_icmsst *= self.round_value((1 - (reducao_icmsst / 100.0)), 5)  # Redução da Base
        base_icmsst *= self.round_value((1 + aliquota_mva / 100.0), 5)  # Aplica MVA

        icmsst = self.round_value((base_icmsst * (icmsst_tax.amount / 100.0)), 5)

        vals = {
            'icms_st_valor': icmsst if icmsst >= 0.0 else 0.0,
            'icms_st_base_calculo': base_icmsst,
        }

        return vals

    @api.multi
    @api.onchange('icms_st_aliquota')
    def compute_tax(self):
        if self.icms_st_aliquota > 0:
            icms_st = self.compute_icms_st(price_base=self.icms_st_aliquota, mva=self.product_mva)
            self.update(icms_st)

    @api.onchange('icms_st_valor_manual', 'icms_valor_manual')
    def compute_cost_extra(self):
        for record in self:
            extra_cost = 0
            total_cost = 0
            if record.icms_st_valor_manual == 0 and record.icms_st_frete_valor_manual == 0 \
                    and record.icms_valor_manual == 0:
                extra_cost = 0
            else:
                extra_cost += (record.icms_st_valor_manual + record.icms_st_frete_valor_manual +
                               record.icms_valor_manual) / record.qty_received
                total_cost += record.product_po_value + record.icms_st_valor_manual + \
                              record.icms_st_frete_valor_manual + record.icms_valor_manual

            record.product_total_cost = total_cost
            record.product_extra_cost = extra_cost

    @api.multi
    @api.onchange('tax_ids')
    def compute_tax(self):
        for record in self:
            for tr in record.tax_ids:
                tax = tr.tax_id
                tax_icms_st = tr.tax_icms_st_id
                if tax_icms_st.domain == 'icmsst':
                    record.icms_st_aliquota = tax.amount
                    record.mva = tr.aliquota_mva

    @api.multi
    def do_change_standard_price(self):
        """ Changes the Standard Price of Product and creates an account move accordingly."""
        for product in self:
            qty_available = product.product_id.qty_available
            if qty_available:
                # Accounting Entries
                current_value_stock = qty_available * product.product_id.standard_price
                diff = product.icms_st_valor_manual + product.icms_st_frete_valor_manual + product.icms_valor_manual
                new_current_value_stock = current_value_stock + diff
                new_price = round(new_current_value_stock / qty_available, 4)
                product_accounts = {prod.id: prod.product_tmpl_id.get_product_accounts() for prod in
                                    product.product_id}

                credit_account_id = product_accounts[product.product_id.id]['stock_valuation'].id
                journal_id = product_accounts[product.product_id.id]['stock_journal'].id,

                move_vals = {
                    'journal_id': product_accounts[product.product_id.id]['stock_journal'].id,
                    'company_id': product.company_id.id,
                    'line_ids': [(0, 0, {
                        'name': _('Custos Adicionais (ICMS / ICMS ST / ICMS ST Frete)  - %s') % (
                            product.product_id.display_name),
                        'account_id': 24,
                        'debit': abs(diff * qty_available),
                        'credit': 0,
                        'product_id': product.product_id.id,
                    }), (0, 0, {
                        'name': _('Custos Adicionais (ICMS / ICMS ST / ICMS ST Frete)  - %s') % (
                            product.product_id.display_name),
                        'account_id': credit_account_id,
                        'debit': 0,
                        'credit': abs(diff * qty_available),
                        'product_id': product.id,
                    })],
                }

                debit_line = (0, 0, {
                    'name': _('Custos Adicionais (ICMS ST / ICMS ST Frete)  - %s') % (product.product_id.display_name),
                    'account_id': 24, 'debit': abs(diff * qty_available), 'credit': 0,
                    'product_id': product.product_id.id, })

                credit_line = (0, 0, {
                        'name': _('Custos Adicionais (ICMS ST / ICMS ST Frete)  - %s') % (
                            product.product_id.display_name), 'account_id': credit_account_id, 'debit': 0,
                        'credit': abs(diff * qty_available), 'product_id': product.id,
                    })
                message = []

                if product.icms_st_valor_manual > 0:
                    icms_st_per_unit = round(product.icms_st_valor_manual / product.product_qty, 4)
                    message.append("Alteração do Vlr Unit do Produto - Vlr Unt Ant R$ %s - Vlr Unt Adic R$ %s"
                                   " Referente à ICMS ST - Custa adicional Referente ao Pedido %s" \
                                   % (product.product_id.standard_price, icms_st_per_unit, product.po_id.name))
                if product.icms_st_frete_valor_manual > 0:
                    icms_st_frete_per_unit = round(product.icms_st_frete_valor_manual / product.product_qty, 4)
                    message.append("Alteração do Vlr Unit do Produto - Vlr Unt Ant R$ %s - Vlr Unt Adic R$ %s"
                                   " Referente à ICMS ST Sobre o Frete - Custa adicional Referente ao Pedido %s" \
                                   % (product.product_id.standard_price, icms_st_frete_per_unit, product.po_id.name))
                if product.icms_valor_manual > 0:
                    icms_per_unit = round(product.icms_valor_manual / product.product_qty, 4)
                    message.append("Alteração do Vlr Unit do Produto - Vlr Unt Ant R$ %s - Vlr Unt Adic R$ %s"
                                   " Referente à  ICMS - Custa adicional Referente ao Pedido %s" \
                                   % (product.product_id.standard_price, icms_per_unit, product.po_id.name))

            product.product_id.write({'standard_price': new_price})

            if len(message) > 0:
                msg = ''
                for t in message:
                    msg += t
                product.product_id.product_tmpl_id.message_post(body=msg)

        return debit_line, credit_line, journal_id