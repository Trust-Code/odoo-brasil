# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo import api, fields, models


class InvoiceEletronic(models.Model):
    _name = 'invoice.eletronic'

    _inherit = ['mail.thread']

    code = fields.Char(u'Código', size=100, required=True)
    name = fields.Char(u'Name', size=100, required=True)
    company_id = fields.Many2one('res.company', u'Company', select=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             string=u'State', default='draft')

    tipo_operacao = fields.Selection([('entrada', 'Entrada'),
                                      ('saida', 'Saída')], u'Tipo emissão')
    model = fields.Selection([('55', 'NFe'), ('65', 'NFCe')], u'Modelo')
    serie = fields.Many2one('l10n_br_account.document.serie', string=u'Série')
    numero = fields.Integer(u'Número')
    numero_controle = fields.Integer(u'Número de Controle')
    data_emissao = fields.Datetime(u'Data emissão')
    data_fatura = fields.Datetime(u'Data Entrada/Saída')
    data_autorizacao = fields.Datetime(u'Data de autorização')

    ambiente = fields.Selection([('homologacao', 'Homologação'),
                                 ('producao', 'Produção')], u'Ambiente')
    finalidade_emissao = fields.Selection([('1', 'Normal'),
                                           ('2', 'Complementar'),
                                           ('3', 'Ajuste'),
                                           ('4', 'Devolução')],
                                          u'Finalidade da emissão')
    consumidor_final = fields.Selection([('0', 'Normal'),
                                         ('1', 'Consumidor')],
                                        u'Indicador de Consumidor Final')

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

    total_tax_icms_id = fields.Many2one('sped.tax.icms', string=u'Total ICMS')
    total_tax_ipi_id = fields.Many2one('sped.tax.ipi', string=u'Total IPI')
    total_tax_ii_id = fields.Many2one('sped.tax.ii',
                                      string=u'Total Imposto de importação')
    total_tax_pis_id = fields.Many2one('sped.tax.pis', string=u'Total PIS')
    total_tax_cofins_id = fields.Many2one('sped.tax.cofins',
                                          string=u'Total Cofins')
    total_tax_issqn_id = fields.Many2one('sped.tax.issqn',
                                         string=u'Total ISSQN')
    total_tax_csll_id = fields.Many2one('sped.tax.csll',
                                        string=u'Total CSLL')
    total_tax_irrf_id = fields.Many2one('sped.tax.irrf', string=u'Total IRRF')
    total_tax_inss_id = fields.Many2one('sped.tax.inss', string=u'Total INSS')

    valor_bruto = fields.Float(u'Valor Produtos')
    valor_frete = fields.Float(u'Valor do frete')
    valor_seguro = fields.Float(u'Valor do seguro')
    valor_desconto = fields.Float(u'Valor do desconto')
    valor_despesas = fields.Float(u'Valor despesas')
    valor_retencoes = fields.Float(u'Retenções')
    valor_BC = fields.Float(u"Valor da Base de Cálculo")
    valor_icms = fields.Float(u"Valor do ICMS")
    valor_icms_deson = fields.Float(u'Valor ICMSDeson')
    valor_bcst = fields.Float(u'Valor BCST')
    valor_st = fields.Float(u'Valor ST')
    valor_ii = fields.Float(u'Valor do Imposto de Importação')
    valor_ipi = fields.Float(u"Valor do IPI")
    valor_pis = fields.Float(u"Valor PIS")
    valor_cofins = fields.Float(u"Valor COFINS")

    valor_final = fields.Float(u'Valor Final')

    transportation_id = fields.Many2one('invoice.transport')

    informacoes_legais = fields.Text(u'Informações legais')
    informacoes_complementar = fields.Text(u'Informações complementares')

    codigo_retorno = fields.Char(string=u'Código Retorno')
    mensagem_retorno = fields.Char(string=u'Mensagem Retorno')

    @api.multi
    def _hook_validation(self):
        """
            Override this method to implement the validations specific
            for the city you need
            @returns list<string> errors
        """
        errors = []
        if not self.serie:
            errors.append(u'Nota Fiscal - Série da nota fiscal')
        if not self.serie.fiscal_document_id:
            errors.append(u'Nota Fiscal - Tipo de documento fiscal')
        if not self.serie.internal_sequence_id:
            errors.append(u'Nota Fiscal - Número da nota fiscal, \
                          a série deve ter uma sequencia interna')

        # Emitente
        if not self.company_id.partner_id.legal_name:
            errors.append(u'Emitente - Razão Social')
        if not self.company_id.partner_id.name:
            errors.append(u'Emitente - Fantasia')
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
        for inv_line in self.eletronic_item_ids:
            if inv_line.product_id:
                if not inv_line.product_id.default_code:
                    errors.append(
                        u'Prod: %s - Código do produto' % (
                            inv_line.product_id.name))
                prod = u"Produto: %s - %s" % (inv_line.product_id.default_code,
                                              inv_line.product_id.name)
                if not inv_line.product_id.name:
                    errors.append(u'%s - Nome do produto' % prod)
                if not inv_line.quantity:
                    errors.append(u'%s - Quantidade' % prod)
                if not inv_line.unit_price:
                    errors.append(u'%s - Preco unitario' % prod)
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
    def _prepare_eletronic_invoice_values(self):
        return {}

    @api.multi
    def action_send_eletronic_invoice(self):
        self.validate_invoice()


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
    company_id = fields.Many2one('res.company', u'Empresa', select=True)
    invoice_eletronic_id = fields.Many2one('invoice.eletronic', u'Documento')

    product_id = fields.Many2one('product.product', string=u'Produto')
    cfop = fields.Char(u'CFOP', size=5)

    uom_id = fields.Many2one('product.uom', u'Unidade de medida')
    quantity = fields.Float(u'Quantidade')
    unit_price = fields.Float(u'Preço Unitário')

    freight_value = fields.Float(u'Frete')
    insurance_value = fields.Float(u'Seguro')
    discount = fields.Float(u'Desconto')
    other_expenses = fields.Float(u'Outras despesas')

    gross_total = fields.Float(u'Valor Bruto')
    total = fields.Float(u'Valor Liquido')

    origem = fields.Selection(
        [('0', '0 - Nacional'),
         ('1', '1 - Estrangeira - Importação direta'),
         ('2', '2 - Estrangeira - Adquirida no mercado interno'),
         ('3', '3 - Nacional, mercadoria ou bem com Conteúdo de Importação \
superior a 40% \e inferior ou igual a 70%'),
         ('4', '4 - Nacional, cuja produção tenha sido feita em conformidade \
com os processos produtivos básicos de que tratam as \
legislações citadas nos Ajustes'),
         ('5', '5 - Nacional, mercadoria ou bem com Conteúdo de Importação \
inferior ou igual a 40%'),
         ('6', '6 - Estrangeira - Importação direta, sem similar nacional, \
constante em lista da CAMEX e gás natural'),
         ('7', '7 - Estrangeira - Adquirida no mercado interno, sem similar \
nacional, constante lista CAMEX e gás natural'),
         ('8', '8 - Nacional, mercadoria ou bem com Conteúdo de Importação \
superior a 70%')],
        u'Origem da mercadoria')
    icms_cst = fields.Selection(
     [
      ('00', '00 - Tributada Integralmente'),
      ('10', '10 - Tributada com ICMS ST'),
      ('20', '20 - Com redução de base de cálculo'),
      ('30', '30 - Isenta ou não tributada e com cobrança do ICMS por \
substituição tributária'),
      ('40', '40 - Isenta'),
      ('41', '41 - Não tributada'),
      ('50', '50 - Suspensão'),
      ('51', '51 - Diferimento'),
      ('60', '60 - ICMS cobrado anteriormente por substituição tributária'),
      ('70', '70 - Com redução de base de cálculo e cobrança do ICMS por \
substituição tributária'),
      ('101', '101 - Tributada pelo Simples Nacional com permissão de \
crédito'),
      ('102', '102 - Tributada pelo Simples Nacional sem permissão de \
crédito'),
      ('103', '103 - Isenção do ICMS no Simples Nacional para faixa de \
receita bruta'),
      ('201', '201 - Tributada pelo Simples Nacional com permissão de crédito \
e com cobrança do ICMS por substituição tributária'),
      ('202', '202 - Tributada pelo Simples Nacional sem permissão de crédito \
e com cobrança do ICMS por substituição tributária'),
      ('203', '203 - Isenção do ICMS no Simples Nacional para faixa de receita \
bruta e com cobrança do ICMS por substituição tributária'),
      ('300', '300 - Imune'),
      ('400', '400 - Não tributada pelo Simples Nacional'),
      ('500', '500 - ICMS cobrado anteriormente por substituição tributária \
(substituído) ou por antecipação'),
      ('900', '900 - Outros'),
      ('90', '90 - Outros')],
     u'Situação tributária do ICMS')
    icms_aliquota = fields.Float(u'Alíquota')
    icms_modalidade_BC = fields.Selection(
        [('0', '0 - Margem Valor Agregado (%)'),
         ('1', '1 - Pauta (Valor)'),
         ('2', '2 - Preço Tabelado Máx. (valor)'),
         ('3', '3 - Valor da operação')],
        u'Modalidade de determinação da BC do ICMS')
    icms_base_calculo = fields.Float(u'Base de cálculo')
    icms_percentual_reducao_bc = fields.Float(u'% Redução Base')
    icms_valor = fields.Float(u'Valor Total')
    icms_value_credit = fields.Float(u"Valor de Cŕedito")
    icms_value_percentual = fields.Float(u'%% de Crédito')

    percentual_mva = fields.Float(u'% MVA')
    aliquota_st = fields.Float(u'Alíquota')
    base_calculo_st = fields.Float(u'Base de cálculo')
    percentual_reducao_bc_st = fields.Float(u'% Redução Base')
    valor_st = fields.Float(u'Valor Total')

    percentual_diferimento = fields.Float(u'% Diferimento')
    valor_diferido = fields.Float(u'Valor Diferido')

    motivo_desoneracao = fields.Float(u'Motivo Desoneração')
    valor_desonerado = fields.Float(u'Valor Desonerado')

    tax_ipi_id = fields.Many2one('sped.tax.ipi', string=u'IPI')
    tax_ii_id = fields.Many2one('sped.tax.ii', string=u'Imposto de importação')
    tax_pis_id = fields.Many2one('sped.tax.pis', string=u'PIS')
    tax_cofins_id = fields.Many2one('sped.tax.cofins', string=u'Cofins')
    tax_issqn_id = fields.Many2one('sped.tax.issqn', string=u'ISSQN')
    tax_csll_id = fields.Many2one('sped.tax.csll', string=u'CSLL')
    tax_irrf_id = fields.Many2one('sped.tax.irrf', string=u'IRRF')
    tax_inss_id = fields.Many2one('sped.tax.inss', string=u'INSS')


class InvoiceTransport(models.Model):
    _name = 'invoice.transport'

    name = fields.Char(u'Nome', size=100)
    company_id = fields.Many2one('res.company', u'Empresa', select=True)

    modalidade_frete = fields.Selection([('0', 'Sem Frete'),
                                         ('1', 'Por conta do destinatário'),
                                         ('2', 'Por conta do emitente'),
                                         ('9', 'Outros')],
                                        u'Modalidade do frete')
    transportadora_id = fields.Many2one('res.partner', u'Transportadora')
    placa_veiculo = fields.Char('Placa do Veiculo', size=7)
    estado_veiculo_id = fields.Many2one('res.country.state', 'UF da Placa')
    cidade_veiculo_id = fields.Many2one(
        'res.state.city', 'Municipio',
        domain="[('state_id', '=', estado_veiculo_id)]")
