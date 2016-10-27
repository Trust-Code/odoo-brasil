# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo import api, fields, models
from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CSOSN_SIMPLES
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS
from odoo.addons.br_account.models.cst import ORIGEM_PROD


class InvoiceEletronic(models.Model):
    _name = 'invoice.eletronic'

    _inherit = ['mail.thread']

    code = fields.Char(u'Código', size=100, required=True)
    name = fields.Char(u'Name', size=100, required=True)
    company_id = fields.Many2one('res.company', u'Company', index=True)
    state = fields.Selection([('draft', 'Draft'), ('error', 'Erro'),
                              ('done', 'Done')],
                             string=u'State', default='draft')

    tipo_operacao = fields.Selection([('entrada', 'Entrada'),
                                      ('saida', 'Saída')], u'Tipo emissão')
    model = fields.Selection([('55', '55 - NFe'),
                              ('65', '65 - NFCe'),
                              ('001', 'NFS-e - Nota Fiscal Paulistana')],
                             u'Modelo')
    serie = fields.Many2one('br_account.document.serie', string=u'Série')
    numero = fields.Integer(u'Número')
    numero_controle = fields.Integer(u'Número de Controle')
    data_emissao = fields.Datetime(u'Data emissão')
    data_fatura = fields.Datetime(u'Data Entrada/Saída')
    data_autorizacao = fields.Char(u'Data de autorização', size=30)

    ambiente = fields.Selection([('homologacao', 'Homologação'),
                                 ('producao', 'Produção')], u'Ambiente')
    finalidade_emissao = fields.Selection(
        [('1', '1 - Normal'),
         ('2', '2 - Complementar'),
         ('3', '3 - Ajuste'),
         ('4', '4 - Devolução')],
        u'Finalidade', help="Finalidade da emissão de NFe")
    invoice_id = fields.Many2one('account.invoice', u'Fatura')
    partner_id = fields.Many2one('res.partner', u'Parceiro')
    partner_shipping_id = fields.Many2one('res.partner', u'Entrega')
    payment_term_id = fields.Many2one('account.payment.term',
                                      string=u'Forma pagamento')
    fiscal_position_id = fields.Many2one('account.fiscal.position',
                                         string=u'Posição Fiscal')

    # parcela_ids = fields.One2many('sped.documentoduplicata',
    #  'documento_id', u'Vencimentos'),

    eletronic_item_ids = fields.One2many('invoice.eletronic.item',
                                         'invoice_eletronic_id',
                                         string=u"Linhas")

    eletronic_event_ids = fields.One2many('invoice.eletronic.event',
                                          'invoice_eletronic_id',
                                          string=u"Eventos")

    valor_bruto = fields.Float(u'Total Produtos')
    valor_frete = fields.Float(u'Total frete')
    valor_seguro = fields.Float(u'Total seguro')
    valor_desconto = fields.Float(u'Total desconto')
    valor_despesas = fields.Float(u'Total despesas')
    valor_bc_icms = fields.Float(u"Base de Cálc ICMS")
    valor_icms = fields.Float(u"Total do ICMS")
    valor_icms_deson = fields.Float(u'ICMS Desoneração')
    valor_bc_icmsst = fields.Float(u'Total Base ST',
                                   help="Total da base de cálculo do ICMS ST")
    valor_icmsst = fields.Float(u'Total ST')
    valor_ii = fields.Float(u'Total II')
    valor_ipi = fields.Float(u"Total IPI")
    valor_pis = fields.Float(u"Total PIS")
    valor_cofins = fields.Float(u"Total COFINS")
    valor_estimado_tributos = fields.Float(u"Tributos estimados")

    valor_servicos = fields.Float(u"Total Serviços")
    valor_bc_issqn = fields.Float(u"Base ISS")
    valor_issqn = fields.Float(u"Total ISS")
    valor_pis_servicos = fields.Float(u"Total PIS Serviços")
    valor_cofins_servicos = fields.Float(u"Total Cofins Serviço")

    valor_retencao_issqn = fields.Float(u"Retenção ISSQN")
    valor_retencao_pis = fields.Float(u"Retenção PIS")
    valor_retencao_cofins = fields.Float(u"Retenção COFINS")
    valor_retencao_irrf = fields.Float(u"Retenção IRRF")
    valor_retencao_csll = fields.Float(u"Retenção CSLL")
    valor_retencao_previdencia = fields.Float(
        u"Retenção Prev.", help="Retenção Previdência Social")

    valor_final = fields.Float(u'Valor Final')

    transportation_id = fields.Many2one('invoice.transport')

    informacoes_legais = fields.Text(u'Informações legais')
    informacoes_complementares = fields.Text(u'Informações complementares')

    codigo_retorno = fields.Char(string=u'Código Retorno')
    mensagem_retorno = fields.Char(string=u'Mensagem Retorno')
    numero_nfe = fields.Char(string="Numero Formatado NFe")

    @api.multi
    def _hook_validation(self):
        """
            Override this method to implement the validations specific
            for the city you need
            @returns list<string> errors
        """
        errors = []
        if not self.serie.fiscal_document_id:
            errors.append(u'Nota Fiscal - Tipo de documento fiscal')
        if not self.serie.internal_sequence_id:
            errors.append(u'Nota Fiscal - Número da nota fiscal, \
                          a série deve ter uma sequencia interna')

        # Emitente
        if not self.company_id.nfe_a1_file:
            errors.append(u'Emitente - Certificado Digital')
        if not self.company_id.nfe_a1_password:
            errors.append(u'Emitente - Senha do Certificado Digital')
        if not self.company_id.partner_id.legal_name:
            errors.append(u'Emitente - Razão Social')
        if not self.company_id.partner_id.cnpj_cpf:
            errors.append(u'Emitente - CNPJ/CPF')
        if not self.company_id.partner_id.street:
            errors.append(u'Emitente / Endereço - Logradouro')
        if not self.company_id.partner_id.number:
            errors.append(u'Emitente / Endereço - Número')
        if not self.company_id.partner_id.zip:
            errors.append(u'Emitente / Endereço - CEP')
        if not self.company_id.partner_id.inscr_est:
            errors.append(u'Emitente / Inscrição Estadual')
        if not self.company_id.partner_id.state_id:
            errors.append(u'Emitente / Endereço - Estado')
        else:
            if not self.company_id.partner_id.state_id.ibge_code:
                errors.append(u'Emitente / Endereço - Cód. do IBGE do estado')
            if not self.company_id.partner_id.state_id.name:
                errors.append(u'Emitente / Endereço - Nome do estado')

        if not self.company_id.partner_id.city_id:
            errors.append(u'Emitente / Endereço - município')
        else:
            if not self.company_id.partner_id.city_id.name:
                errors.append(u'Emitente / Endereço - Nome do município')
            if not self.company_id.partner_id.city_id.ibge_code:
                errors.append(u'Emitente/Endereço - Cód. do IBGE do município')

        if not self.company_id.partner_id.country_id:
            errors.append(u'Emitente / Endereço - país')
        else:
            if not self.company_id.partner_id.country_id.name:
                errors.append(u'Emitente / Endereço - Nome do país')
            if not self.company_id.partner_id.country_id.bc_code:
                errors.append(u'Emitente / Endereço - Código do BC do país')

        partner = self.partner_id
        company = self.company_id
        # Destinatário
        if partner.is_company and not partner.legal_name:
            errors.append(u'Destinatário - Razão Social')

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.cnpj_cpf:
                errors.append(u'Destinatário - CNPJ/CPF')

        if not partner.street:
            errors.append(u'Destinatário / Endereço - Logradouro')

        if not partner.number:
            errors.append(u'Destinatário / Endereço - Número')

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.zip:
                errors.append(u'Destinatário / Endereço - CEP')

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.state_id:
                errors.append(u'Destinatário / Endereço - Estado')
            else:
                if not partner.state_id.ibge_code:
                    errors.append(u'Destinatário / Endereço - Código do IBGE \
                                  do estado')
                if not partner.state_id.name:
                    errors.append(u'Destinatário / Endereço - Nome do estado')

        if partner.country_id.id == company.partner_id.country_id.id:
            if not partner.city_id:
                errors.append(u'Destinatário / Endereço - Município')
            else:
                if not partner.city_id.name:
                    errors.append(u'Destinatário / Endereço - Nome do \
                                  município')
                if not partner.city_id.ibge_code:
                    errors.append(u'Destinatário / Endereço - Código do IBGE \
                                  do município')

        if not partner.country_id:
            errors.append(u'Destinatário / Endereço - País')
        else:
            if not partner.country_id.name:
                errors.append(u'Destinatário / Endereço - Nome do país')
            if not partner.country_id.bc_code:
                errors.append(u'Destinatário / Endereço - Cód. do BC do país')

        # produtos
        for eletr in self.eletronic_item_ids:
            if eletr.product_id:
                if not eletr.product_id.default_code:
                    errors.append(
                        u'Prod: %s - Código do produto' % (
                            eletr.product_id.name))
        return errors

    @api.multi
    def validate_invoice(self):
        self.ensure_one()
        errors = self._hook_validation()
        if len(errors) > 0:
            print errors
            msg = u"\n".join(
                [u"Por favor corrija os erros antes de prosseguir"] + errors)
            raise UserError(msg)

    @api.multi
    def action_post_validate(self):
        pass

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        return {}

    @api.multi
    def action_send_eletronic_invoice(self):
        pass

    @api.multi
    def action_back_to_draft(self):
        self.state = 'draft'

    @api.multi
    def cron_send_nfe(self):
        inv_obj = self.env['invoice.eletronic'].with_context({
            'lang': self.env.user.lang, 'tz': self.env.user.tz})
        nfes = inv_obj.search([('state', '=', 'draft')])
        for item in nfes:
            item.action_send_eletronic_invoice()


class InvoiceEletronicEvent(models.Model):
    _name = 'invoice.eletronic.event'
    _order = 'id desc'

    code = fields.Char(string=u'Código', readonly=True)
    name = fields.Char(string=u'Mensagem', readonly=True)
    invoice_eletronic_id = fields.Many2one('invoice.eletronic',
                                           string=u"Fatura Eletrônica")


class InvoiceEletronicItem(models.Model):
    _name = 'invoice.eletronic.item'

    name = fields.Char(u'Nome', size=100)
    company_id = fields.Many2one('res.company', u'Empresa', index=True)
    invoice_eletronic_id = fields.Many2one('invoice.eletronic', u'Documento')

    product_id = fields.Many2one('product.product', string=u'Produto')
    tipo_produto = fields.Selection([('product', 'Produto'),
                                     ('service', 'Serviço')],
                                    string="Tipo Produto")
    cfop = fields.Char(u'CFOP', size=5)
    ncm = fields.Char(u'NCM', size=10)

    uom_id = fields.Many2one('product.uom', u'Unidade de medida')
    quantidade = fields.Float(u'Quantidade')
    preco_unitario = fields.Float(u'Preço Unitário')

    frete = fields.Float(u'Frete')
    seguro = fields.Float(u'Seguro')
    desconto = fields.Float(u'Desconto')
    outras_despesas = fields.Float(u'Outras despesas')

    tributos_estimados = fields.Float(u'Valor Estimado Tributos')

    valor_bruto = fields.Float(u'Valor Bruto')
    valor_liquido = fields.Float(u'Valor Liquido')
    indicador_total = fields.Selection(
        [('0', '0 - Não'), ('1', '1 - Sim')],
        string="Compõe Total da Nota?", default='1')

    origem = fields.Selection(ORIGEM_PROD, u'Origem mercadoria')
    icms_cst = fields.Selection(
        CST_ICMS + CSOSN_SIMPLES, u'Situação tributária')
    icms_aliquota = fields.Float(u'Alíquota')
    icms_tipo_base = fields.Selection(
        [('0', '0 - Margem Valor Agregado (%)'),
         ('1', '1 - Pauta (Valor)'),
         ('2', '2 - Preço Tabelado Máx. (valor)'),
         ('3', '3 - Valor da operação')],
        u'Modalidade BC do ICMS')
    icms_base_calculo = fields.Float(u'Base de cálculo')
    icms_aliquota_reducao_base = fields.Float(u'% Redução Base')
    icms_valor = fields.Float(u'Valor Total')
    icms_valor_credito = fields.Float(u"Valor de Cŕedito")
    icms_aliquota_credito = fields.Float(u'% de Crédito')

    icms_st_tipo_base = fields.Selection(
        [('0', '0- Preço tabelado ou máximo  sugerido'),
         ('1', '1 - Lista Negativa (valor)'),
         ('2', '2 - Lista Positiva (valor)'),
         ('3', '3 - Lista Neutra (valor)'),
         ('4', '4 - Margem Valor Agregado (%)'), ('5', '5 - Pauta (valor)')],
        'Tipo Base ICMS ST', required=True, default='4')
    icms_st_aliquota_mva = fields.Float(u'% MVA')
    icms_st_aliquota = fields.Float(u'Alíquota')
    icms_st_base_calculo = fields.Float(u'Base de cálculo')
    icms_st_aliquota_reducao_base = fields.Float(u'% Redução Base')
    icms_st_valor = fields.Float(u'Valor Total')

    icms_aliquota_diferimento = fields.Float(u'% Diferimento')
    icms_valor_diferido = fields.Float(u'Valor Diferido')

    icms_motivo_desoneracao = fields.Float(u'Motivo Desoneração')
    icms_valor_desonerado = fields.Float(u'Valor Desonerado')

    # ----------- IPI -------------------
    classe_enquadramento = fields.Char(u'Classe enq.', size=5,
                                       help="Classe Enquadramento no IPI")
    codigo_enquadramento = fields.Char(u'Código enq.', size=4,
                                       help="Código Enquadramento no IPI")
    ipi_cst = fields.Selection(CST_IPI, string=u'Situação tributária do ICMS')
    ipi_aliquota = fields.Float(u'Alíquota')
    ipi_base_calculo = fields.Float(u'Base de cálculo')
    ipi_reducao_bc = fields.Float(u'% Redução Base')
    ipi_valor = fields.Float(u'Valor Total')

    # ----------- II ----------------------
    ii_base_calculo = fields.Float(u'Base de cálculo')
    ii_aliquota = fields.Float(u'Alíquota II')
    ii_valor_despesas = fields.Float(u'Despesas aduaneiras')
    ii_valor = fields.Float(u'Imposto de importação')
    ii_valor_iof = fields.Float(u'IOF')

    # ------------ PIS ---------------------
    pis_cst = fields.Selection(CST_PIS_COFINS, u'Situação tributária')
    pis_aliquota = fields.Float(u'Alíquota')
    pis_base_calculo = fields.Float(u'Base de cálculo')
    pis_valor = fields.Float(u'Valor Total')

    # ------------ COFINS ------------
    cofins_cst = fields.Selection(CST_PIS_COFINS, u'Situação tributária')
    cofins_aliquota = fields.Float(u'Alíquota')
    cofins_base_calculo = fields.Float(u'Base de cálculo')
    cofins_valor = fields.Float(u'Valor Total')

    # ----------- ISSQN -------------
    issqn_codigo = fields.Char(u'Código', size=10)
    issqn_aliquota = fields.Float(u'Alíquota')
    issqn_base_calculo = fields.Float(u'Base de cálculo')
    issqn_valor = fields.Float(u'Valor Total')
    issqn_valor_retencao = fields.Float(u'Valor retenção')


class InvoiceTransport(models.Model):
    _name = 'invoice.transport'

    name = fields.Char(u'Nome', size=100)
    company_id = fields.Many2one('res.company', u'Empresa', index=True)

    modalidade_frete = fields.Selection([('0', '0 - Sem Frete'),
                                         ('1', '1 - Por conta destinatário'),
                                         ('2', '2 - Por conta do emitente'),
                                         ('9', '9 - Outros')],
                                        u'Modalidade do frete')
    transportadora_id = fields.Many2one('res.partner', u'Transportadora')
    placa_veiculo = fields.Char('Placa do Veiculo', size=7)
    estado_veiculo_id = fields.Many2one('res.country.state', 'UF da Placa')
    cidade_veiculo_id = fields.Many2one(
        'res.state.city', 'Municipio',
        domain="[('state_id', '=', estado_veiculo_id)]")
