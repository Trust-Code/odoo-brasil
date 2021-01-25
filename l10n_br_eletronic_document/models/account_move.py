import re
from datetime import datetime
from random import SystemRandom

from odoo import api, fields, models
from odoo.exceptions import UserError


TYPE2EDOC = {
    'out_invoice': 'saida',        # Customer Invoice
    'in_invoice': 'entrada',          # Vendor Bill
    'out_refund': 'entrada',        # Customer Refund
    'in_refund': 'saida',          # Vendor Refund
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['eletronic.document'].search_count(
                [('move_id', '=', item.id)])

    def _get_default_policy(self):
        if self.env.context.get('default_type', '') == 'out_invoice':
            return 'directly'
        if self.env.context.get('default_type', '') == 'in_invoice':
            return 'manually'

    total_edocs = fields.Integer(string="Total NFe", compute=_compute_total_edocs)

    l10n_br_edoc_policy = fields.Selection(
        [('directly', 'Emitir agora'),
         ('after_payment', 'Emitir após pagamento'),
         ('manually', 'Manualmente')], string="Nota Eletrônica", default=_get_default_policy)

    @api.model
    def _autopost_draft_entries(self):
        records = self.search([
            ('state', '=', 'draft'),
            ('date', '<=', fields.Date.today()),
            ('auto_post', '=', True),
        ])
        for item in records:
            item.action_post()
            self.env.cr.commit()

    def _validate_for_eletronic_document(self):
        errors = []
        for move in self:
            if not move.company_id.l10n_br_certificate:
                errors.append('Cadastro da Empresa - Certificado Digital')
            if not move.company_id.l10n_br_cert_password:
                errors.append('Cadastro da Empresa - Senha do Certificado Digital')
            if not move.company_id.partner_id.l10n_br_legal_name:
                errors.append('Cadastro da Empresa - Razão Social')
            if not move.company_id.partner_id.l10n_br_cnpj_cpf:
                errors.append('Cadastro da Empresa - CNPJ/CPF')
            if not move.company_id.partner_id.street:
                errors.append('Cadastro da Empresa / Endereço - Logradouro')
            if not move.company_id.partner_id.l10n_br_number:
                errors.append('Cadastro da Empresa / Endereço - Número')
            if not move.company_id.partner_id.zip or len(
                    re.sub(r"\D", "", self.company_id.partner_id.zip)) != 8:
                errors.append('Cadastro da Empresa / Endereço - CEP')
            if not move.company_id.partner_id.state_id:
                errors.append('Cadastro da Empresa / Endereço - Estado')
            else:
                if not move.company_id.partner_id.state_id.l10n_br_ibge_code:
                    errors.append('Cadastro da Empresa / Endereço - Cód. do IBGE do estado')
                if not move.company_id.partner_id.state_id.name:
                    errors.append('Cadastro da Empresa / Endereço - Nome do estado')

            if not move.company_id.partner_id.city_id:
                errors.append('Cadastro da Empresa / Endereço - município')
            else:
                if not move.company_id.partner_id.city_id.name:
                    errors.append('Cadastro da Empresa / Endereço - Nome do município')
                if not move.company_id.partner_id.city_id.l10n_br_ibge_code:
                    errors.append('Cadastro da Empresa/Endereço - Cód. do IBGE do município')

            if not move.company_id.partner_id.country_id:
                errors.append('Cadastro da Empresa / Endereço - país')
            else:
                if not move.company_id.partner_id.country_id.name:
                    errors.append('Cadastro da Empresa / Endereço - Nome do país')
                if not move.company_id.partner_id.country_id.l10n_br_ibge_code:
                    errors.append('Cadastro da Empresa / Endereço - Código do BC do país')

            has_products = has_services = False
            # produtos
            for eletr in move.invoice_line_ids:
                if eletr.product_id.type == 'service':
                    has_services = True
                if eletr.product_id.type in ('consu', 'product'):
                    has_products = True
                prod = "Produto: %s - %s" % (eletr.product_id.default_code,
                                            eletr.product_id.name)
                if not eletr.product_id.default_code:
                    errors.append(
                        'Prod: %s - Código do produto' % (
                            eletr.product_id.name))

                if not move.fiscal_position_id:
                    errors.append('Configure a posição fiscal')
                if move.company_id.l10n_br_accountant_id and not \
                    move.company_id.l10n_br_accountant_id.l10n_br_cnpj_cpf:
                    errors.append('Cadastro da Empresa / CNPJ do escritório contabilidade')

            if has_products and not move.company_id.l10n_br_nfe_sequence:
                errors.append('Configure a sequência para numeração de NFe')
            if has_services and not move.company_id.l10n_br_nfe_service_sequence:
                errors.append('Configure a sequência para numeração de NFe de serviço')

            partner = move.partner_id.commercial_partner_id
            company = move.company_id
            # Destinatário
            if partner.is_company and not partner.l10n_br_legal_name:
                errors.append('Cliente - Razão Social')

            if partner.country_id.id == company.partner_id.country_id.id:
                if not partner.l10n_br_cnpj_cpf:
                    errors.append('Cliente - CNPJ/CPF')

            if not partner.street:
                errors.append('Cliente / Endereço - Logradouro')

            if not partner.l10n_br_number:
                errors.append('Cliente / Endereço - Número')

            if partner.country_id.id == company.partner_id.country_id.id:
                if not partner.zip or len(
                        re.sub(r"\D", "", partner.zip)) != 8:
                    errors.append('Cliente / Endereço - CEP')

            if partner.country_id.id == company.partner_id.country_id.id:
                if not partner.state_id:
                    errors.append('Cliente / Endereço - Estado')
                else:
                    if not partner.state_id.l10n_br_ibge_code:
                        errors.append('Cliente / Endereço - Código do IBGE \
                                    do estado')
                    if not partner.state_id.name:
                        errors.append('Cliente / Endereço - Nome do estado')

            if partner.country_id.id == company.partner_id.country_id.id:
                if not partner.city_id:
                    errors.append('Cliente / Endereço - Município')
                else:
                    if not partner.city_id.name:
                        errors.append('Cliente / Endereço - Nome do \
                                    município')
                    if not partner.city_id.l10n_br_ibge_code:
                        errors.append('Cliente / Endereço - Código do IBGE \
                                    do município')

            if not partner.country_id:
                errors.append('Cliente / Endereço - País')
            else:
                if not partner.country_id.name:
                    errors.append('Cliente / Endereço - Nome do país')
                if not partner.country_id.l10n_br_ibge_code:
                    errors.append('Cliente / Endereço - Cód. do BC do país')

        if len(errors) > 0:
            msg = "\n".join(
                ["Por favor corrija os erros antes de prosseguir"] + errors)
            raise UserError(msg)

    def _prepare_eletronic_line_vals(self, invoice_lines):
        lines = []
        for line in invoice_lines:

            vals = line.get_eletronic_line_vals()

            lines.append((0, 0, vals))

        return lines

    def _prepare_eletronic_doc_vals(self, invoice_lines):
        invoice = self
        num_controle = int(''.join([str(SystemRandom().randrange(9))
                                    for i in range(8)]))
        numero_nfe = numero_rps = 0
        if self.company_id.l10n_br_nfe_sequence:
            numero_nfe = self.company_id.l10n_br_nfe_sequence.next_by_id()
        if self.company_id.l10n_br_nfe_service_sequence:
            numero_rps = self.company_id.l10n_br_nfe_service_sequence.next_by_id()
        vals = {
            'name': invoice.name,
            'move_id': invoice.id,
            'company_id': invoice.company_id.id,
            'schedule_user_id': self.env.user.id,
            'state': 'draft',
            'tipo_operacao': TYPE2EDOC[invoice.type],
            'numero_controle': num_controle,
            'data_emissao': datetime.now(),
            'data_agendada': invoice.invoice_date,
            'finalidade_emissao': '1',
            'ambiente': invoice.company_id.l10n_br_tipo_ambiente,
            'partner_id': invoice.partner_id.id,
            'payment_term_id': invoice.invoice_payment_term_id.id,
            'fiscal_position_id': invoice.fiscal_position_id.id,
            'natureza_operacao': invoice.fiscal_position_id.name,
            'ind_pres': invoice.fiscal_position_id.ind_pres,
            'informacoes_complementares': invoice.narration,
            'numero_fatura': invoice.name,
            'fatura_bruto': invoice.amount_total,
            'fatura_desconto': 0.0,
            'fatura_liquido': invoice.amount_total,
            'pedido_compra': invoice.ref,
            'serie_documento': invoice.fiscal_position_id.serie_nota_fiscal,
            'numero': numero_nfe,
            'numero_rps': numero_rps,
            'valor_frete': invoice.l10n_br_delivery_amount,
            'valor_seguro': invoice.l10n_br_insurance_amount,
            'valor_despesas': invoice.l10n_br_expense_amount,
        }
        vals['cod_regime_tributario'] = '1' if invoice.company_id.l10n_br_tax_regime == 'simples' else '3'

        # Indicador de destino
        vals['ind_dest'] = '1'
        if invoice.company_id.state_id != invoice.commercial_partner_id.state_id:
            vals['ind_dest'] = '2'
        if invoice.company_id.country_id != invoice.commercial_partner_id.country_id:
            vals['ind_dest'] = '3'

        # Indicador IE Destinatário
        ind_ie_dest = False
        if invoice.commercial_partner_id.is_company:
            if invoice.commercial_partner_id.l10n_br_inscr_est:
                ind_ie_dest = '1'
            elif invoice.commercial_partner_id.state_id.code in ('AM', 'BA', 'CE',
                                                                 'GO', 'MG', 'MS',
                                                                 'MT', 'PE', 'RN',
                                                                 'SP'):
                ind_ie_dest = '9'
            elif invoice.commercial_partner_id.country_id.code != 'BR':
                ind_ie_dest = '9'
            else:
                ind_ie_dest = '2'
        else:
            ind_ie_dest = '9'
        if invoice.commercial_partner_id.l10n_br_indicador_ie_dest:
            ind_ie_dest = invoice.commercial_partner_id.l10n_br_indicador_ie_dest
        vals['ind_ie_dest'] = ind_ie_dest

        # Indicador Consumidor Final
        if invoice.commercial_partner_id.is_company:
            if vals['ind_ie_dest'] == '9':
                vals['ind_final'] = '1'
            else:
                vals['ind_final'] = '0'
        else:
            vals['ind_final'] = '1'

        if invoice.fiscal_position_id.ind_final:
            vals['ind_final'] = invoice.fiscal_position_id.ind_final

        iest_id = invoice.company_id.l10n_br_iest_ids.filtered(
            lambda x: x.state_id == invoice.commercial_partner_id.state_id)
        if iest_id:
            vals['iest'] = iest_id.name

        total_produtos = total_servicos = 0.0
        bruto_produtos = bruto_servicos = 0.0
        total_desconto = 0
        for inv_line in invoice_lines:
            total_desconto += round(inv_line.price_unit * inv_line.quantity * inv_line.discount / 100, 2)
            if inv_line.product_id.type == 'service':
                total_servicos += inv_line.price_total
                bruto_servicos += round(inv_line.quantity * inv_line.price_unit, 2)
            else:
                total_produtos += inv_line.price_total
                bruto_produtos += round(inv_line.quantity * inv_line.price_unit, 2)

        vals.update({
            'valor_bruto': bruto_produtos + bruto_servicos,
            'valor_servicos': total_servicos,
            'valor_produtos': total_produtos,
            'valor_desconto': total_desconto,
            'valor_final': total_produtos + total_servicos,
        })

        return vals

    def sum_line_taxes(self, vals):
        lines = vals.get("document_line_ids")
        return {
            'valor_icms': sum(line[2].get("icms_valor", 0) for line in lines),
            'valor_icmsst': sum(line[2].get("icms_st_valor", 0) for line in lines),
            'valor_ipi': sum(line[2].get("ipi_valor", 0) for line in lines),
            'pis_valor': sum(line[2].get("pis_valor", 0) for line in lines),
            'cofins_valor': sum(line[2].get("cofins_valor", 0) for line in lines),
            'valor_ii': sum(line[2].get("ii_valor", 0) for line in lines),
            'valor_bc_icms': sum(line[2].get("icms_base_calculo", 0) for line in lines),
            'valor_bc_icmsst': sum(line[2].get("icms_st_base_calculo", 0) for line in lines),
            'pis_valor_retencao': sum(line[2].get("pis_valor_retencao", 0) for line in lines),
            'cofins_valor_retencao': sum(line[2].get("cofins_valor_retencao", 0) for line in lines),
            'irrf_base_calculo': sum(line[2].get("irrf_base_calculo", 0) for line in lines),
            'irrf_valor_retencao': sum(line[2].get("irrf_valor_retencao", 0) for line in lines),
            'csll_base_calculo': sum(line[2].get("csll_base_calculo", 0) for line in lines),
            'csll_valor_retencao': sum(line[2].get("csll_valor_retencao", 0) for line in lines),
            'inss_base_calculo': sum(line[2].get("inss_base_calculo", 0) for line in lines),
            'inss_valor_retencao': sum(line[2].get("inss_valor_retencao", 0) for line in lines),
        }

    def action_create_eletronic_document(self):
        for move in self:
            invoice_lines = move.invoice_line_ids.filtered(
                lambda x: not x.is_delivery_expense_or_insurance()
            )
            services = invoice_lines.filtered(lambda x: x.product_id.type == 'service')
            if services:
                self._create_service_eletronic_document(move, services)

            products = invoice_lines.filtered(lambda x: x.product_id.type != 'service')
            if products:
                self._create_product_eletronic_document(move, products)

    def _create_service_eletronic_document(self, move, services):
        vals = move._prepare_eletronic_doc_vals(services)
        vals['model'] = 'nfse'
        vals['document_line_ids'] = move._prepare_eletronic_line_vals(services)
        vals.update(self.sum_line_taxes(vals))
        self.env['eletronic.document'].create(vals)

    def _create_product_eletronic_document(self, move, products):
        vals = move._prepare_eletronic_doc_vals(products)
        vals['model'] = 'nfe'

        if self.type == 'out_refund':
            vals['related_document_ids'] = self._create_related_doc(vals)

        vals['document_line_ids'] = move._prepare_eletronic_line_vals(products)
        vals.update(self.sum_line_taxes(vals))
        self.env['eletronic.document'].create(vals)

    def _create_related_doc(self, vals):
        related_move_id = self.env['account.move'].search([
            ('reversal_move_id', 'in', self.id)], limit=1)

        doc = self.env['eletronic.document'].search([
            ('move_id', '=', related_move_id.id),
            ('model', '=', vals['model']),
            ('state', '=', 'done')
        ], limit=1, order='id desc')

        if doc:
            related_doc = self.env['nfe.related.document'].create({
                'move_related_id': related_move_id.id,
                'document_type': 'nfe',
                'access_key': doc.chave_nfe,
            })
            return related_doc

    def action_post(self):
        moves = self.filtered(lambda x: x.l10n_br_edoc_policy == 'directly' and x.type != 'entry')
        moves._validate_for_eletronic_document()
        res = super(AccountMove, self).action_post()
        moves.action_create_eletronic_document()
        return res

    def action_view_edocs(self):
        if self.total_edocs == 1:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'l10n_br_eletronic_document', 'action_view_eletronic_document')
            dummy, view_id = self.env['ir.model.data'].get_object_reference(
                'l10n_br_eletronic_document', 'view_eletronic_document_form')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            vals['view_id'] = (view_id, 'sped.eletronic.doc.form')
            vals['views'][1] = (view_id, 'form')
            vals['views'] = [vals['views'][1], vals['views'][0]]
            edoc = self.env['eletronic.document'].search(
                [('move_id', '=', self.id)], limit=1)
            vals['res_id'] = edoc.id
            return vals
        else:
            dummy, act_id = self.env['ir.model.data'].get_object_reference(
                'l10n_br_eletronic_document', 'action_view_eletronic_document')
            vals = self.env['ir.actions.act_window'].browse(act_id).read()[0]
            vals['domain'] = [('move_id', '=', self.id)]
            return vals


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def get_eletronic_line_vals(self):
        pis = self.move_id.line_ids.filtered(lambda x: x.tax_line_id.domain == 'pis')
        cofins = self.move_id.line_ids.filtered(lambda x: x.tax_line_id.domain == 'cofins')
        iss = self.move_id.line_ids.filtered(lambda x: x.tax_line_id.domain == 'iss')
        csll = self.move_id.line_ids.filtered(lambda x: x.tax_line_id.domain == 'csll')
        irpj = self.move_id.line_ids.filtered(lambda x: x.tax_line_id.domain == 'irpj')
        inss = self.move_id.line_ids.filtered(lambda x: x.tax_line_id.domain == 'inss')

        ipi = self.move_id.line_ids.filtered(lambda x: x.tax_line_id.domain == 'ipi')

        fiscal_pos = self.move_id.fiscal_position_id

        vals = {
            'name': self.name,
            'product_id': self.product_id.id,
            'eletronic_document_id': self.id,
            'company_id': self.company_id.id,
            'tipo_produto': 'service' if self.product_id.type == 'service' else 'product',
            # 'cfop': self.cfop_id.code,
            'uom_id': self.product_uom_id.id,
            'quantidade': self.quantity,
            'preco_unitario': self.price_unit,
            'valor_bruto': round(self.quantity * self.price_unit, 2),
            'desconto': round(self.quantity * self.price_unit, 2) - self.price_subtotal,
            'valor_liquido': self.price_total,
            'origem': self.product_id.l10n_br_origin,
            #  'tributos_estimados': self.tributos_estimados,
            'ncm': self.product_id.l10n_br_ncm_id.code,
            'cest': self.product_id.l10n_br_cest,
            'pedido_compra': self.ref,
            # 'item_pedido_compra': self.item_pedido_compra,
            # - ICMS -
            'icms_cst': fiscal_pos.csosn_icms,
            # 'icms_aliquota': self.icms_aliquota,
            # 'icms_tipo_base': self.icms_tipo_base,
            # 'icms_aliquota_reducao_base': self.icms_aliquota_reducao_base,
            # 'icms_base_calculo': self.icms_base_calculo,
            # 'icms_valor': self.icms_valor,
            # - ICMS ST -
            # 'icms_st_aliquota': self.icms_st_aliquota,
            # 'icms_st_aliquota_mva': self.icms_st_aliquota_mva,
            # 'icms_st_aliquota_reducao_base': self.\
            # icms_st_aliquota_reducao_base,
            # 'icms_st_base_calculo': self.icms_st_base_calculo,
            # 'icms_st_valor': self.icms_st_valor,
            # # - Simples Nacional -
            'icms_aliquota_credito': fiscal_pos.icms_aliquota_credito,
            'icms_valor_credito': round(self.price_total * fiscal_pos.icms_aliquota_credito / 100, 2),
            # - IPI -
            'ipi_cst': '99',
            'ipi_aliquota': ipi.tax_line_id.amount or 0,
            'ipi_base_calculo': self.price_total or 0,
            'ipi_valor': round(self.price_total * ipi.tax_line_id.amount / 100, 2),
            # 'ipi_reducao_bc': self.ipi_reducao_bc,
            # - II -
            # 'ii_base_calculo': self.ii_base_calculo,
            # 'ii_valor_despesas': self.ii_valor_despesas,
            # 'ii_valor': self.ii_valor,
            # 'ii_valor_iof': self.ii_valor_iof,
            # - PIS -
            'pis_cst': '49',
            'pis_aliquota': pis.tax_line_id.amount or 0,
            'pis_base_calculo': self.price_total or 0,
            'pis_valor': round(self.price_total * pis.tax_line_id.amount / 100, 2),
            # 'pis_valor_retencao':
            # abs(self.pis_valor) if self.pis_valor < 0 else 0,
            # - COFINS -
            'cofins_cst': '49',
            'cofins_aliquota':  cofins.tax_line_id.amount or 0,
            'cofins_base_calculo': self.price_total or 0,
            'cofins_valor': round(self.price_total * cofins.tax_line_id.amount / 100, 2),
            # 'cofins_valor_retencao':
            # abs(self.cofins_valor) if self.cofins_valor < 0 else 0,
            # - ISS -
            'item_lista_servico': self.product_id.service_type_id.code,
            'codigo_servico_municipio': self.product_id.service_code,
            'iss_aliquota': iss.tax_line_id.amount or 0,
            'iss_base_calculo': self.price_subtotal or 0,
            'iss_valor': round(self.price_subtotal * iss.tax_line_id.amount / 100, 2),
            # 'iss_valor_retencao':
            # abs(self.iss_valor) if self.iss_valor < 0 else 0,
            # - RETENÇÔES -
            'csll_aliquota': csll.tax_line_id.amount or 0,
            'csll_base_calculo': self.price_total or 0,
            'csll_valor': round(self.price_total * csll.tax_line_id.amount / 100, 2),
            # abs(self.csll_valor) if self.csll_valor < 0 else 0,
            'irpj_aliquota':  irpj.tax_line_id.amount or 0,
            'irpj_base_calculo': self.price_total or 0,
            'irpj_valor': round(self.price_total * irpj.tax_line_id.amount / 100, 2),
            # 'irrf_base_calculo': self.irrf_base_calculo,
            # 'irrf_aliquota': abs(self.irrf_aliquota),
            # 'irrf_valor_retencao':
            # abs(self.irrf_valor) if self.irrf_valor < 0 else 0,
            'inss_base_calculo': self.price_subtotal or 0,
            'inss_aliquota': abs(inss.tax_line_id.amount or 0),
            'inss_valor_retencao': abs(
                round(self.price_subtotal * inss.tax_line_id.amount / 100, 2)
            ),
            'frete': self.l10n_br_delivery_amount,
            'seguro': self.l10n_br_insurance_amount,
            'outras_despesas': self.l10n_br_expense_amount,
        }
        cfop = fiscal_pos.l10n_br_cfop_id.code or '5101'

        if self.move_id.type in ['in_invoice', 'out_refund']:
            if self.move_id.company_id.state_id == self.move_id.commercial_partner_id.state_id:
                cfop = '1' + cfop[1:]
            else:
                cfop = '2' + cfop[1:]
        elif self.move_id.type in ['out_invoice', 'in_refund']:
            if self.move_id.company_id.state_id == self.move_id.commercial_partner_id.state_id:
                cfop = '5' + cfop[1:]
            else:
                cfop = '6' + cfop[1:]

        vals['cfop'] = cfop
        return vals
