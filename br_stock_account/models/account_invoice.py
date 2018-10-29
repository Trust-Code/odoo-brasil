# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'br.localization.filtering']

    l10n_br_fiscal_position_type = fields.Selection(
        related='fiscal_position_id.l10n_br_fiscal_type',
        readonly=True, oldname='fiscal_position_type')

    @api.multi
    def copy(self, default=None):
        new_acc_inv = super(AccountInvoice, self).copy(default)
        for i in range(len(new_acc_inv.invoice_line_ids)):
            new_acc_inv.invoice_line_ids[i].l10n_br_import_declaration_ids = \
                self.invoice_line_ids[i].l10n_br_import_declaration_ids
        return new_acc_inv

    @api.one
    @api.depends('invoice_line_ids.price_subtotal',
                 'invoice_line_ids.price_total',
                 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        lines = self.invoice_line_ids

        self.l10n_br_total_seguro = sum(l.l10n_br_valor_seguro for l in lines)
        self.l10n_br_total_frete = sum(l.l10n_br_valor_frete for l in lines)
        self.l10n_br_total_despesas = sum(
            l.l10n_br_outras_despesas for l in lines)
        self.amount_total = (
            self.l10n_br_total_bruto - self.l10n_br_total_desconto +
            self.l10n_br_total_tax + self.l10n_br_total_frete +
            self.l10n_br_total_seguro + self.l10n_br_total_despesas)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = self.amount_total * sign
        self.amount_total_signed = self.amount_total * sign

    l10n_br_total_seguro = fields.Float(
        string='Seguro ( + )', digits=dp.get_precision('Account'),
        compute="_compute_amount", oldname='total_seguro')
    l10n_br_total_despesas = fields.Float(
        string='Despesas ( + )', digits=dp.get_precision('Account'),
        compute="_compute_amount", oldname='total_despesas')
    l10n_br_total_frete = fields.Float(
        string='Frete ( + )', digits=dp.get_precision('Account'),
        compute="_compute_amount", oldname='total_frete')

    # Transporte
    freight_responsibility = fields.Selection(
        [('0', '0 - Contratação do Frete por conta do Remetente (CIF)'),
         ('1', '1 - Contratação do Frete por conta do Destinatário (FOB)'),
         ('2', '2 - Contratação do Frete por conta de Terceiros'),
         ('3', '3 - Transporte Próprio por conta do Remetente'),
         ('4', '4 - Transporte Próprio por conta do Destinatário'),
         ('9', '9 - Sem Ocorrência de Transporte')],
        u'Modalidade do frete', default="9")
    shipping_supplier_id = fields.Many2one('res.partner', 'Transportadora')
    vehicle_plate = fields.Char(u'Placa do Veículo', size=7)
    vehicle_state_id = fields.Many2one('res.country.state', 'UF da Placa')
    vehicle_rntc = fields.Char('RNTC', size=20)

    tow_plate = fields.Char('Placa do Reboque', size=7)
    tow_state_id = fields.Many2one(
        'res.country.state', 'UF da Placa do Reboque')
    tow_rntc = fields.Char('RNTC Reboque', size=20)

    weight = fields.Float(string='Peso Bruto', help="O peso bruto em Kg.")
    weight_net = fields.Float(u'Peso Líquido', help=u"O peso líquido em Kg.")
    number_of_packages = fields.Integer(u'Nº Volumes')
    kind_of_packages = fields.Char(u'Espécie', size=60)
    brand_of_packages = fields.Char('Marca', size=60)
    notation_of_packages = fields.Char(u'Numeração', size=60)

    # Exportação
    uf_saida_pais_id = fields.Many2one(
        'res.country.state', domain=[('country_id.code', '=', 'BR')],
        string=u"UF Saída do País")
    local_embarque = fields.Char('Local de Embarque', size=60)
    local_despacho = fields.Char('Local de Despacho', size=60)

    def _prepare_edoc_vals(self, inv, inv_lines, serie_id):
        res = super(AccountInvoice, self)._prepare_edoc_vals(
            inv, inv_lines, serie_id)
        res['valor_frete'] = inv.l10n_br_total_frete
        res['valor_despesas'] = inv.l10n_br_total_despesas
        res['valor_seguro'] = inv.l10n_br_total_seguro
        res['modalidade_frete'] = inv.freight_responsibility
        res['transportadora_id'] = inv.shipping_supplier_id.id
        res['placa_veiculo'] = (inv.vehicle_plate or '').upper()
        res['uf_veiculo'] = inv.vehicle_state_id.code
        res['rntc'] = inv.vehicle_rntc

        res['reboque_ids'] = [(0, None, {
            'uf_veiculo': inv.tow_state_id.code,
            'rntc': inv.tow_rntc,
            'placa_veiculo': (inv.tow_plate or '').upper(),
        })]

        res['volume_ids'] = [(0, None, {
            'peso_bruto': inv.weight,
            'peso_liquido': inv.weight_net,
            'quantidade_volumes': inv.number_of_packages,
            'especie': inv.kind_of_packages,
            'marca': inv.brand_of_packages,
            'numeracao': inv.notation_of_packages,
        })]

        res['uf_saida_pais_id'] = inv.uf_saida_pais_id.id
        res['local_embarque'] = inv.local_embarque
        res['local_despacho'] = inv.local_despacho

        return res

    def _prepare_edoc_item_vals(self, invoice_line):
        vals = super(AccountInvoice, self). \
            _prepare_edoc_item_vals(invoice_line)
        vals['frete'] = invoice_line.l10n_br_valor_frete
        vals['seguro'] = invoice_line.l10n_br_valor_seguro
        vals['outras_despesas'] = invoice_line.l10n_br_outras_despesas
        return vals


class AccountInvoiceLine(models.Model):
    _name = 'account.invoice.line'
    _inherit = ['account.invoice.line', 'br.localization.filtering']

    l10n_br_valor_frete = fields.Float(
        '(+) Frete', digits=dp.get_precision('Account'), default=0.00,
        oldname='valor_frete')
    l10n_br_valor_seguro = fields.Float(
        '(+) Seguro', digits=dp.get_precision('Account'), default=0.00,
        oldname='valor_seguro')
    l10n_br_outras_despesas = fields.Float(
        '(+) Despesas', digits=dp.get_precision('Account'), default=0.00,
        oldname='outras_despesas')

    def _prepare_tax_context(self):
        res = super(AccountInvoiceLine, self)._prepare_tax_context()
        res.update({
            'valor_frete': self.l10n_br_valor_frete,
            'valor_seguro': self.l10n_br_valor_seguro,
            'outras_despesas': self.l10n_br_outras_despesas,
            'ii_despesas': self.l10n_br_ii_valor_despesas,
        })
        return res

    @api.one
    @api.depends('l10n_br_valor_frete', 'l10n_br_valor_seguro',
                 'l10n_br_outras_despesas')
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()

        total = (self.l10n_br_valor_bruto - self.l10n_br_valor_desconto +
                 self.l10n_br_valor_frete + self.l10n_br_valor_seguro +
                 self.l10n_br_outras_despesas)
        self.update({'price_total': total})
