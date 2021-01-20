import re
import json
import requests
import base64
import copy
import time
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from .focus_nfse import check_nfse_api

from odoo.addons.l10n_br_account.models.cst import (
    CST_ICMS, CST_PIS_COFINS, CSOSN_SIMPLES, CST_IPI, ORIGEM_PROD)

_logger = logging.getLogger(__name__)


STATE = {'draft': [('readonly', False)]}


class EletronicDocument(models.Model):
    _name = 'eletronic.document'
    _description = 'Eletronic documents (NFE, NFSe)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name', size=30, readonly=True, states=STATE)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency", readonly=True, states=STATE)
    identifier = fields.Char(
        string="Identificador", readonly=True, states=STATE)

    partner_id = fields.Many2one('res.partner')
    partner_cpf_cnpj = fields.Char(string="CNPJ/CPF", size=20)

    commercial_partner_id = fields.Many2one(
        'res.partner', string='Commercial Entity',
        related='partner_id.commercial_partner_id', store=True)
    partner_shipping_id = fields.Many2one(
        'res.partner', string=u'Entrega', readonly=True, states=STATE)

    move_id = fields.Many2one(
        'account.move', string='Fatura', readonly=True, states=STATE)

    document_line_ids = fields.One2many(
        'eletronic.document.line', 'eletronic_document_id', string="Linhas", copy=True)

    @api.depends('document_line_ids')
    def _compute_tax_totals(self):
        for doc in self:
            doc.pis_base_calculo = sum([x.pis_base_calculo for x in doc.document_line_ids])
            doc.pis_valor = sum([x.pis_valor for x in doc.document_line_ids])
            doc.pis_valor_retencao = sum([x.pis_valor_retencao for x in doc.document_line_ids])

            doc.cofins_base_calculo = sum([x.cofins_base_calculo for x in doc.document_line_ids])
            doc.cofins_valor = sum([x.cofins_valor for x in doc.document_line_ids])
            doc.cofins_valor_retencao = sum([x.cofins_valor_retencao for x in doc.document_line_ids])

            doc.iss_base_calculo = sum([x.iss_base_calculo for x in doc.document_line_ids])
            doc.iss_valor = sum([x.iss_valor for x in doc.document_line_ids])
            doc.iss_valor_retencao = sum([x.iss_valor_retencao for x in doc.document_line_ids])

            doc.irpj_base_calculo = sum([x.irpj_base_calculo for x in doc.document_line_ids])
            doc.irpj_valor = sum([x.irpj_valor for x in doc.document_line_ids])
            doc.irpj_valor_retencao = sum([x.irpj_valor_retencao for x in doc.document_line_ids])

            doc.csll_base_calculo = sum([x.csll_base_calculo for x in doc.document_line_ids])
            doc.csll_valor = sum([x.csll_valor for x in doc.document_line_ids])
            doc.csll_valor_retencao = sum([x.csll_valor_retencao for x in doc.document_line_ids])

            doc.inss_base_calculo = sum([x.inss_base_calculo for x in doc.document_line_ids])
            doc.inss_valor_retencao = sum([x.inss_valor_retencao for x in doc.document_line_ids])

    # ------------ PIS ---------------------
    pis_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    pis_valor = fields.Monetary(
        string='Valor PIS', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    pis_valor_retencao = fields.Monetary(
        string='Valor Retido', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)

    # ------------ COFINS ------------
    cofins_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    cofins_valor = fields.Monetary(
        string='Valor COFINS', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    cofins_valor_retencao = fields.Monetary(
        string='Valor Retido', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)

    # ----------- ISS -------------
    iss_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    iss_valor = fields.Monetary(
        string='Valor ISS', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    iss_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)

    # ------------ CSLL ------------
    csll_base_calculo = fields.Monetary(
        string='Base CSLL', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    csll_valor = fields.Monetary(
        string='Valor CSLL', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    csll_valor_retencao = fields.Monetary(
        string='Retenção CSLL', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)

     # ------------ IRPJ ------------
    irpj_base_calculo = fields.Monetary(
        string='Base IRPJ', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    irpj_valor = fields.Monetary(
        string='Valor IRPJ', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)
    irpj_valor_retencao = fields.Monetary(
        string='Retenção IRPJ', digits='Account',
        readonly=True, states=STATE, store=True, compute=_compute_tax_totals)

    # ------------ Retencoes ------------   
    irrf_base_calculo = fields.Monetary(
        string='Base IRRF', digits='Account',
        readonly=True, states=STATE)
    irrf_valor_retencao = fields.Monetary(
        string='Valor IRRF', digits='Account',
        readonly=True, states=STATE)
    inss_base_calculo = fields.Monetary(
        string='Base INSS', digits='Account',
        readonly=True, states=STATE)
    inss_valor_retencao = fields.Monetary(
        string='Valor INSS', digits='Account',
        readonly=True, states=STATE)

    valor_produtos = fields.Monetary(
        string='Valor Produtos', readonly=True, states=STATE)
    valor_servicos = fields.Monetary(
        string='Valor Serviços', readonly=True, states=STATE)

    valor_final = fields.Monetary(
        string='Valor Final', readonly=True, states=STATE)

    state = fields.Selection(
        [('draft', 'Provisório'),
         ('edit', 'Editar'),
         ('error', 'Erro'),
         ('processing', 'Em processamento'),
         ('denied', 'Denegado'),
         ('done', 'Enviado'),
         ('cancel', 'Cancelado')],
        string=u'State', default='draft', readonly=True, states=STATE,
        track_visibility='always', copy=False)
    schedule_user_id = fields.Many2one(
        'res.users', string="Agendado por", readonly=True,
        track_visibility='always')
    tipo_operacao = fields.Selection(
        [('entrada', 'Entrada'),
         ('saida', 'Saída')],
        string=u'Tipo de Operação', readonly=True, states=STATE)
    model = fields.Selection(
        [('nfe', '55 - NFe'),
         ('nfce', '65 - NFCe'),
         ('nfse', 'NFS-e - Nota Fiscal de Servico')],
        string=u'Modelo', readonly=True, states=STATE)
    # serie = fields.Many2one(
    #     'br_account.document.serie', string=u'Série',
    #     readonly=True, states=STATE)
    serie_documento = fields.Char(string='Série Documento', size=6)
    numero = fields.Integer(
        string='Número', readonly=True, states=STATE, copy=False)
    numero_rps = fields.Integer(
        string='Número RPS', readonly=True, states=STATE, copy=False)
    numero_controle = fields.Integer(
        string='Número de Controle', readonly=True, states=STATE, copy=False)
    data_agendada = fields.Date(
        string='Data agendada', default=fields.Date.today,
        readonly=True, states=STATE)
    data_emissao = fields.Datetime(
        string='Data emissão', readonly=True, states=STATE, copy=False)
    data_autorizacao = fields.Char(
        string='Data de autorização', size=30, readonly=True, states=STATE, copy=False)
    ambiente = fields.Selection(
        [('homologacao', 'Homologação'),
         ('producao', 'Produção')],
        string='Ambiente', readonly=True, states=STATE)
    finalidade_emissao = fields.Selection(
        [('1', u'1 - Normal'),
         ('2', u'2 - Complementar'),
         ('3', u'3 - Ajuste'),
         ('4', u'4 - Devolução')],
        string=u'Finalidade', help=u"Finalidade da emissão de NFe",
        readonly=True, states=STATE)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Condição pagamento',
        readonly=True, states=STATE)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string=u'Posição Fiscal',
        readonly=True, states=STATE)
    natureza_operacao = fields.Char(
        string='Natureza da Operação', size=60, readonly=True, states=STATE)
    # eletronic_event_ids = fields.One2many(
    #     'invoice.eletronic.event', 'invoice_eletronic_id', string=u"Eventos",
    #     readonly=True, states=STATE)
    valor_bruto = fields.Monetary(
        string='Valor Bruto', readonly=True, states=STATE)
    valor_frete = fields.Monetary(
        string=u'Total Frete', readonly=True, states=STATE)
    valor_seguro = fields.Monetary(
        string=u'Total Seguro', readonly=True, states=STATE)
    valor_desconto = fields.Monetary(
        string=u'Total Desconto', readonly=True, states=STATE)
    valor_despesas = fields.Monetary(
        string=u'Total Despesas', readonly=True, states=STATE)
    valor_bc_icms = fields.Monetary(
        string=u"Base ICMS", readonly=True, states=STATE)
    valor_icms = fields.Monetary(
        string=u"Total do ICMS", readonly=True, states=STATE)
    valor_icms_deson = fields.Monetary(
        string=u'ICMS Desoneração', readonly=True, states=STATE)
    valor_bc_icmsst = fields.Monetary(
        string=u'Total Base ST', help=u"Total da base de cálculo do ICMS ST",
        readonly=True, states=STATE)
    valor_icmsst = fields.Monetary(
        string=u'Total ST', readonly=True, states=STATE)
    valor_ii = fields.Monetary(
        string=u'Total II', readonly=True, states=STATE)
    valor_ipi = fields.Monetary(
        string=u"Total IPI", readonly=True, states=STATE)

    @api.depends('document_line_ids')
    def _compute_valor_estimado_tributos(self):
        self.valor_estimado_tributos = sum(line.tributos_estimados for line in self.document_line_ids)
    valor_estimado_tributos = fields.Monetary(
        string=u"Tributos Estimados", readonly=True, states=STATE,
        compute="_compute_valor_estimado_tributos")

    valor_servicos = fields.Monetary(
        string=u"Total Serviços", readonly=True, states=STATE)

    informacoes_legais = fields.Text(
        string='Informações legais', readonly=True, states=STATE)
    informacoes_complementares = fields.Text(
        string='Informações complementares', readonly=True, states=STATE)

    codigo_retorno = fields.Char(
        string='Código Retorno', readonly=True, states=STATE,
        track_visibility='onchange', copy=False)
    mensagem_retorno = fields.Char(
        string='Mensagem Retorno', readonly=True, states=STATE,
        track_visibility='onchange', copy=False)
    numero_nfe = fields.Char(
        string="Numero Formatado NFe", readonly=True, states=STATE)

    xml_to_send = fields.Binary(string="Xml a Enviar", readonly=True)
    xml_to_send_name = fields.Char(
        string="Nome xml a ser enviado", size=100, readonly=True)

    email_sent = fields.Boolean(
        string="Email enviado", default=False, readonly=True, states=STATE)
    salvar_xml_enviado = fields.Boolean(
        string="Salvar Xml Enviado?", default=False, readonly=True, states=STATE)
    # payment_mode_id = fields.Many2one(
    #     'l10n_br.payment.mode', string='Modo de Pagamento',
    #     readonly=True, states=STATE)
    iest = fields.Char(string="IE Subst. Tributário")
    cod_regime_tributario = fields.Selection(
        [('1', 'Simples Nacional'),
         ('2', 'Simples - Excesso de receita'),
         ('3', 'Regime Normal')], string="Cód. Regime Trib.")
    ind_final = fields.Selection([
        ('0', u'Não'),
        ('1', u'Sim')
    ], u'Consumidor Final', readonly=True, states=STATE, required=False,
        help=u'Indica operação com Consumidor final.', default='0')
    ind_pres = fields.Selection([
        ('0', u'Não se aplica'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('5', u'Operação presencial, fora do estabelecimento'),
        ('9', u'Operação não presencial, outros'),
    ], u'Indicador de Presença', readonly=True, states=STATE, required=False,
        help=u'Indicador de presença do comprador no\n'
             u'estabelecimento comercial no momento\n'
             u'da operação.', default='0')
    ind_dest = fields.Selection([
        ('1', u'1 - Operação Interna'),
        ('2', u'2 - Operação Interestadual'),
        ('3', u'3 - Operação com exterior')],
        string=u"Indicador Destinatário", readonly=True, states=STATE)
    ind_ie_dest = fields.Selection([
        ('1', u'1 - Contribuinte ICMS'),
        ('2', u'2 - Contribuinte Isento de Cadastro'),
        ('9', u'9 - Não Contribuinte')],
        string=u"Indicador IE Dest.", help=u"Indicador da IE do desinatário",
        readonly=True, states=STATE)
    tipo_emissao = fields.Selection([
        ('1', u'1 - Emissão normal'),
        ('2', u'2 - Contingência FS-IA, com impressão do DANFE em formulário \
         de segurança'),
        ('3', u'3 - Contingência SCAN'),
        ('4', u'4 - Contingência DPEC'),
        ('5', u'5 - Contingência FS-DA, com impressão do DANFE em \
         formulário de segurança'),
        ('6', u'6 - Contingência SVC-AN'),
        ('7', u'7 - Contingência SVC-RS'),
        ('9', u'9 - Contingência off-line da NFC-e')],
        string=u"Tipo de Emissão", readonly=True, states=STATE, default='1')

    # Transporte
    data_entrada_saida = fields.Datetime(
        string="Data Entrega", help="Data para saída/entrada das mercadorias")
    modalidade_frete = fields.Selection(
        [('0', '0 - Contratação do Frete por conta do Remetente (CIF)'),
         ('1', '1 - Contratação do Frete por conta do Destinatário (FOB)'),
         ('2', '2 - Contratação do Frete por conta de Terceiros'),
         ('3', '3 - Transporte Próprio por conta do Remetente'),
         ('4', '4 - Transporte Próprio por conta do Destinatário'),
         ('9', '9 - Sem Ocorrência de Transporte')],
        string=u'Modalidade do frete', default="9",
        readonly=True, states=STATE)
    transportadora_id = fields.Many2one(
        'res.partner', string=u"Transportadora", readonly=True, states=STATE)
    placa_veiculo = fields.Char(
        string=u'Placa do Veículo', size=7, readonly=True, states=STATE)
    uf_veiculo = fields.Char(
        string=u'UF da Placa', size=2, readonly=True, states=STATE)
    rntc = fields.Char(
        string="RNTC", size=20, readonly=True, states=STATE,
        help=u"Registro Nacional de Transportador de Carga")

    reboque_ids = fields.One2many(
        'nfe.reboque', 'eletronic_document_id',
        string=u"Reboques", readonly=True, states=STATE)
    volume_ids = fields.One2many(
        'nfe.volume', 'eletronic_document_id',
        string=u"Volumes", readonly=True, states=STATE)

    # Exportação
    uf_saida_pais_id = fields.Many2one(
        'res.country.state', domain=[('country_id.code', '=', 'BR')],
        string="UF Saída do País", readonly=True, states=STATE)
    local_embarque = fields.Char(
        string='Local de Embarque', size=60, readonly=True, states=STATE)
    local_despacho = fields.Char(
        string='Local de Despacho', size=60, readonly=True, states=STATE)

    # Cobrança
    numero_fatura = fields.Char(
        string=u"Fatura", readonly=True, states=STATE)
    fatura_bruto = fields.Monetary(
        string=u"Valor Original", readonly=True, states=STATE)
    fatura_desconto = fields.Monetary(
        string=u"Desconto", readonly=True, states=STATE)
    fatura_liquido = fields.Monetary(
        string=u"Valor Líquido", readonly=True, states=STATE)

    duplicata_ids = fields.One2many(
        'nfe.duplicata', 'eletronic_document_id',
        string=u"Duplicatas", readonly=True, states=STATE)

    # Compras
    nota_empenho = fields.Char(
        string="Nota de Empenho", size=22, readonly=True, states=STATE)
    pedido_compra = fields.Char(
        string="Pedido Compra", size=60, readonly=True, states=STATE)
    contrato_compra = fields.Char(
        string="Contrato Compra", size=60, readonly=True, states=STATE)

    sequencial_evento = fields.Integer(
        string=u"Sequêncial Evento", default=1, readonly=True, states=STATE, copy=False)
    recibo_nfe = fields.Char(
        string=u"Recibo NFe", size=50, readonly=True, states=STATE, copy=False)
    chave_nfe = fields.Char(
        string=u"Chave NFe", size=50, readonly=True, states=STATE, copy=False)
    chave_nfe_danfe = fields.Char(
        string=u"Chave Formatado", compute="_compute_format_danfe_key")
    protocolo_nfe = fields.Char(
        string=u"Protocolo", size=50, readonly=True, states=STATE,
        help=u"Protocolo de autorização da NFe", copy=False)
    nfe_processada = fields.Binary(
        string=u"Xml da NFe", readonly=True, copy=False)
    nfe_processada_name = fields.Char(
        string=u"Xml da NFe", size=100, readonly=True, copy=False)

    nfse_url = fields.Char(
        string="URL da NFe", size=500, readonly=True, copy=False)
    nfse_pdf = fields.Binary(
        string="PDF da NFe", readonly=True, copy=False)
    nfse_pdf_name = fields.Char(
        string="PDF da NFe name", size=100, readonly=True, copy=False)

    valor_icms_uf_remet = fields.Monetary(
        string=u"ICMS Remetente", readonly=True, states=STATE,
        help=u'Valor total do ICMS Interestadual para a UF do Remetente')
    valor_icms_uf_dest = fields.Monetary(
        string=u"ICMS Destino", readonly=True, states=STATE,
        help=u'Valor total do ICMS Interestadual para a UF de destino')
    valor_icms_fcp_uf_dest = fields.Monetary(
        string=u"Total ICMS FCP", readonly=True, states=STATE,
        help=u'Total total do ICMS relativo Fundo de Combate à Pobreza (FCP) \
        da UF de destino')

    # NFC-e
    qrcode_hash = fields.Char(string='QR-Code hash')
    qrcode_url = fields.Char(string='QR-Code URL')
    metodo_pagamento = fields.Selection(
        [('01', 'Dinheiro'),
         ('02', 'Cheque'),
         ('03', 'Cartão de Crédito'),
         ('04', 'Cartão de Débito'),
         ('05', 'Crédito Loja'),
         ('10', 'Vale Alimentação'),
         ('11', 'Vale Refeição'),
         ('12', 'Vale Presente'),
         ('13', 'Vale Combustível'),
         ('15', 'Boleto Bancário'),
         ('90', 'Sem pagamento'),
         ('99', 'Outros')],
        string="Forma de Pagamento", default="01")
    valor_pago = fields.Monetary(string='Valor pago')
    troco = fields.Monetary(string='Troco')

    # Documentos Relacionados
    related_document_ids = fields.One2many(
        'nfe.related.document', 'eletronic_document_id',
        'Documentos Fiscais Relacionados', readonly=True, states=STATE)

    # CARTA DE CORRECAO
    cartas_correcao_ids = fields.One2many(
        'carta.correcao.eletronica.evento', 'eletronic_document_id',
        string="Cartas de Correção", readonly=True, states=STATE)

    discriminacao_servicos = fields.Char(compute='_compute_discriminacao')

    cert_state = fields.Selection(
        [('not_loaded', 'Not loaded'),
         ('expired', 'Expired'),
         ('invalid_password', 'Invalid Password'),
         ('unknown', 'Unknown'),
         ('valid', 'Valid')],
        string='Estado do Certificado', related='company_id.l10n_br_cert_state',
        readonly=True)

    def _compute_discriminacao(self):
        for item in self:
            descricao = ''
            for line in item.document_line_ids:
                if line.name:
                    descricao += line.name.replace('\n', '|') + '|'
            if item.informacoes_legais:
                descricao += item.informacoes_legais.replace('\n', '|')
            if item.informacoes_complementares:
                descricao += item.informacoes_complementares.replace('\n', '|')
            item.discriminacao_servicos = descricao

    def _compute_legal_information(self):
        fiscal_ids = self.move_id.fiscal_observation_ids.filtered(
            lambda x: x.tipo == 'fiscal')
        obs_ids = self.move_id.fiscal_observation_ids.filtered(
            lambda x: x.tipo == 'observacao')

        prod_obs_ids = self.env['br_account.fiscal.observation'].browse()
        for item in self.move_id.invoice_line_ids:
            prod_obs_ids |= item.product_id.fiscal_observation_ids

        fiscal_ids |= prod_obs_ids.filtered(lambda x: x.tipo == 'fiscal')
        obs_ids |= prod_obs_ids.filtered(lambda x: x.tipo == 'observacao')

        fiscal = self._compute_msg(fiscal_ids) + (
            self.invoice_id.fiscal_comment or '')

        ncm_tax_related = 'Valor Aprox. dos Tributos R$ %s. Fonte: IBPT\n' % \
                          (str(self.valor_estimado_tributos))

        observacao = ncm_tax_related + self._compute_msg(obs_ids) + (
            self.invoice_id.comment or '')

        self.informacoes_legais = fiscal
        self.informacoes_complementares = observacao

    def _compute_msg(self, observation_ids):
        from jinja2.sandbox import SandboxedEnvironment
        mako_template_env = SandboxedEnvironment(
            block_start_string="<%",
            block_end_string="%>",
            variable_start_string="${",
            variable_end_string="}",
            comment_start_string="<%doc>",
            comment_end_string="</%doc>",
            line_statement_prefix="%",
            line_comment_prefix="##",
            trim_blocks=True,               # do not output newline after
            autoescape=True,                # XML/HTML automatic escaping
        )
        mako_template_env.globals.update({
            'str': str,
            'datetime': datetime,
            'len': len,
            'abs': abs,
            'min': min,
            'max': max,
            'sum': sum,
            'filter': filter,
            'map': map,
            'round': round,
            # dateutil.relativedelta is an old-style class and cannot be
            # instanciated wihtin a jinja2 expression, so a lambda "proxy" is
            # is needed, apparently.
            'relativedelta': lambda *a, **kw: relativedelta(*a, **kw),
            # adding format amount
            # now we can format values like currency on fiscal observation
            'format_amount': lambda amount, currency,
            context=self._context: format_amount(self.env, amount, currency),
        })
        mako_safe_env = copy.copy(mako_template_env)
        mako_safe_env.autoescape = False

        result = ''
        for item in observation_ids:
            if item.document_id and item.document_id.code != self.model:
                continue
            template = mako_safe_env.from_string(tools.ustr(item.message))
            variables = self._get_variables_msg()
            render_result = template.render(variables)
            result += render_result + '\n'
        return result

    def _get_variables_msg(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'invoice': self.move_id
        }

    def generate_correction_letter(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "wizard.carta.correcao.eletronica",
            "views": [[False, "form"]],
            "name": _("Carta de Correção"),
            "target": "new",
            "context": {'default_eletronic_doc_id': self.id},
        }

    def validate_invoice(self):
        self.ensure_one()
        errors = self._hook_validation()
        if len(errors) > 0:
            msg = u"\n".join(
                [u"Por favor corrija os erros antes de prosseguir"] + errors)
            self.sudo().unlink()
            raise UserError(msg)

    def action_post_validate(self):
        self._compute_legal_information()

    def _prepare_eletronic_invoice_item(self, item, invoice):
        return {}

    def _prepare_eletronic_invoice_values(self):
        return {}

    def action_back_to_draft(self):
        self.state = 'draft'

    def action_edit_edoc(self):
        self.state = 'edit'

    def can_unlink(self):
        if self.state not in ('done', 'cancel', 'denied'):
            return True
        return False

    def unlink(self):
        for item in self:
            if not item.can_unlink():
                raise UserError(
                    _('Documento Eletrônico enviado - Proibido excluir'))
        super(EletronicDocument, self).unlink()

    def log_exception(self, exc):
        self.write({
            'codigo_retorno': -1,
            'mensagem_retorno': str(exc),
            'state': 'error',
        })

    def notify_user(self):
        try:
            activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
        except ValueError:
            activity_type_id = False
        self.env['mail.activity'].create({
            'activity_type_id': activity_type_id,
            'note': _('Verifique a notas fiscal - emissão com problemas'),
            'user_id': self.schedule_user_id.id,
            'res_id': self.id,
            'res_model_id': self.env.ref(
                'l10n_br_eletronic_document.model_eletronic_document').id,
        })

    def _get_state_to_send(self):
        return ('draft',)

    def cron_send_nfe(self, limit=50):
        inv_obj = self.env['eletronic.document'].with_context({
            'lang': self.env.user.lang, 'tz': self.env.user.tz})
        states = self._get_state_to_send()
        nfes = inv_obj.search([('state', 'in', states),
                               ('data_agendada', '<=', fields.Date.today())],
                              limit=limit)
        for item in nfes:
            try:
                _logger.info('Sending edoc id: %s (number: %s) by cron' % (
                    item.id, item.numero))
                item.action_send_eletronic_invoice()
            except Exception as e:
                item.log_exception(e)
                item.notify_user()
                _logger.error(
                    'Erro no envio de documento eletrônico', exc_info=True)
            finally:
                self.env.cr.commit()

    def _find_attachment_ids_email(self):
        atts = []
        attachment_obj = self.env['ir.attachment']
        xml_id = attachment_obj.create(dict(
            name=self.nfe_processada_name,
            datas=self.nfe_processada,
            mimetype='text/xml',
            res_model='account.move',
            res_id=self.move_id.id,
        ))
        atts.append(xml_id.id)
        if self.nfse_pdf:
            pdf_id = attachment_obj.create(dict(
                name=self.nfse_pdf_name,
                datas=self.nfse_pdf,
                mimetype='application/pdf',
                res_model='account.move',
                res_id=self.move_id.id,
            ))
            atts.append(pdf_id.id)
            return atts

        danfe_report = self.env['ir.actions.report'].search(
            [('report_name', '=', 'l10n_br_eletronic_document.main_template_br_nfse_danfpse')])
        report_service = danfe_report.xml_id
        danfse, dummy = self.env.ref(report_service).render_qweb_pdf([self.id])
        report_name = safe_eval(danfe_report.print_report_name,
                                {'object': self, 'time': time})
        filename = "%s.%s" % (report_name, "pdf")
        if danfse:
            danfe_id = attachment_obj.create(dict(
                name=filename,
                datas=base64.b64encode(danfse),
                mimetype='application/pdf',
                res_model='account.move',
                res_id=self.move_id.id,
            ))
            atts.append(danfe_id.id)

        return atts

    def send_email_nfe(self):
        mail = self.company_id.l10n_br_nfe_email_template
        if not mail:
            raise UserError(_('Modelo de email padrão não configurado'))
        atts = self._find_attachment_ids_email()
        _logger.info('Sending e-mail for e-doc %s (number: %s)' % (
            self.id, self.numero))

        values = mail.generate_email([self.move_id.id])[self.move_id.id]
        subject = values.pop('subject')
        values.pop('body')
        values.pop('attachment_ids')
        values.pop('res_id')
        values.pop('model')
        # Hack - Those attachments are being encoded twice,
        # so lets decode to message_post encode again
        new_items = []
        for item in values.get('attachments', []):
            new_items.append((item[0], base64.b64decode(item[1])))
        values['attachments'] = new_items
        self.move_id.message_post(
            body=values['body_html'], subject=subject,
            message_type='email', subtype='mt_comment', email_layout_xmlid='mail.mail_notification_paynow',
            attachment_ids=atts + mail.attachment_ids.ids, **values)

    def send_email_nfe_queue(self):
        after = datetime.now() + timedelta(days=-10)
        nfe_queue = self.env['eletronic.document'].search(
            [('data_emissao', '>=', after),
             ('email_sent', '=', False),
             ('state', '=', 'done')], limit=5)
        for nfe in nfe_queue:
            nfe.send_email_nfe()
            nfe.email_sent = True

    def _create_attachment(self, prefix, event, data):
        file_name = '%s-%s.xml' % (
            prefix, datetime.now().strftime('%Y-%m-%d-%H-%M'))
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(data.encode()),
                'description': '',
                'res_model': 'eletronic.document',
                'res_id': event.id
            })

    def generate_dict_values(self):
        dict_docs = []
        for doc in self:
            partner = doc.commercial_partner_id

            emissor = {
                'cnpj': re.sub('[^0-9]', '', doc.company_id.l10n_br_cnpj_cpf or ''),
                'inscricao_municipal': doc.company_id.l10n_br_inscr_mun,
                'codigo_municipio': '%s%s' % (
                    doc.company_id.state_id.l10n_br_ibge_code,
                    doc.company_id.city_id.l10n_br_ibge_code),
            }
            tomador = {
                'cnpj_cpf': re.sub(
                    '[^0-9]', '', partner.l10n_br_cnpj_cpf or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.l10n_br_inscr_mun or ''),
                'empresa': partner.is_company,
                'nome_fantasia': partner.name,
                'razao_social': partner.l10n_br_legal_name or partner.name,
                'telefone': re.sub('[^0-9]', '', doc.partner_id.phone or ''),
                'email': doc.partner_id.email,
                'endereco': {
                    'logradouro': partner.street,
                    'numero': partner.l10n_br_number,
                    'bairro': partner.l10n_br_district,
                    'complemento': partner.street2,
                    'cep': re.sub('[^0-9]', '', partner.zip or ''),
                    'codigo_municipio': '%s%s' % (
                        partner.state_id.l10n_br_ibge_code,
                        partner.city_id.l10n_br_ibge_code),
                    'uf': partner.state_id.code,
                }
            }
            items = []
            for line in doc.document_line_ids:
                aliquota = line.iss_aliquota / 100
                unitario = round(line.valor_liquido / line.quantidade, 2)
                items.append({
                    'name': line.product_id.name,
                    'cst_servico': '0',
                    'codigo_servico': line.item_lista_servico,
                    'cnae_servico': line.codigo_cnae,
                    'codigo_servico_municipio': line.codigo_servico_municipio,
                    'aliquota': aliquota,
                    'base_calculo': round(line.iss_base_calculo, 2),
                    'valor_unitario': unitario,
                    'quantidade': int(line.quantidade),
                    'valor_total': round(line.valor_liquido, 2),
                })
            outra_cidade = doc.company_id.city_id.id != partner.city_id.id
            outro_estado = doc.company_id.state_id.id != partner.state_id.id
            outro_pais = doc.company_id.country_id.id != partner.country_id.id

            data = {
                'nfe_reference': doc.id,
                'ambiente': doc.ambiente,
                'emissor': emissor,
                'tomador': tomador,
                'numero': "%06d" % doc.identifier,
                'outra_cidade': outra_cidade,
                'outro_estado': outro_estado,
                'outro_pais': outro_pais,
                'regime_tributario': doc.company_id.l10n_br_tax_regime,
                'itens_servico': items,
                'data_emissao': doc.data_emissao.strftime('%Y-%m-%d'),
                'serie': doc.serie_documento or '',
                'numero_rps': doc.numero_rps,
                'discriminacao': doc.discriminacao_servicos,
                'valor_servico': round(doc.valor_servicos, 2),
                'base_calculo': round(doc.iss_base_calculo, 2),
                'valor_iss': round(doc.iss_valor, 2),
                'valor_total': round(doc.valor_final, 2),
                'iss_valor_retencao': round(doc.iss_valor_retencao, 2),
                'inss_valor_retencao': round(doc.inss_valor_retencao, 2),
                'valor_carga_tributaria': round(doc.valor_estimado_tributos, 2) or '',
                'fonte_carga_tributaria': 'IBPT',
                'iss_retido': True if doc.iss_valor_retencao > 0.0 else False,
                'aedf': doc.company_id.l10n_br_aedf,
                'client_id': doc.company_id.l10n_br_client_id,
                'client_secret': doc.company_id.l10n_br_client_secret,
                'user_password': doc.company_id.l10n_br_user_password,
                'observacoes': doc.informacoes_complementares,
            }
            dict_docs.append(data)
        return dict_docs

    def _update_document_values(self):
        self.write({
            'data_emissao': datetime.now(),
            'schedule_user_id': self.env.user.id,
        })

    def action_send_eletronic_invoice(self):
        self._update_document_values()
        company = self.mapped('company_id').with_context({'bin_size': False})

        certificate = company.l10n_br_certificate
        password = company.l10n_br_cert_password
        doc_values = self.generate_dict_values()

        response = {}
        cod_municipio = doc_values[0]['emissor']['codigo_municipio']
        if  cod_municipio == '4205407':
            from .nfse_florianopolis import send_api
            response = send_api(certificate, password, doc_values)
        elif cod_municipio == '3550308':
            from .nfse_paulistana import send_api
            response = send_api(certificate, password, doc_values)
        elif cod_municipio == '3106200':
            from .nfse_bh import send_api
            for doc in doc_values:
                doc['data_emissao'] = self.data_emissao.strftime('%Y-%m-%dT%H:%M:%S')
                doc['valor_pis'] = self.pis_valor_retencao
                doc['valor_cofins'] = self.cofins_valor_retencao
                doc['valor_inss'] = self.inss_valor_retencao
                doc['valor_ir'] = self.irrf_valor_retencao
                doc['valor_csll'] = self.csll_valor_retencao
            response = send_api(certificate, password, doc_values)
        else:
            from .focus_nfse import send_api
            response = send_api(
                company.l10n_br_nfse_token_acess,
                doc_values[0]['ambiente'], doc_values)

        if response['code'] in (200, 201):
            vals = {
                'protocolo_nfe': response['entity']['protocolo_nfe'],
                'numero': response['entity']['numero_nfe'],
                'state': 'done',
                'codigo_retorno': '100',
                'mensagem_retorno': 'Nota emitida com sucesso!',
                'nfe_processada_name':  "NFe%08d.xml" % response['entity']['numero_nfe'],
                'nfse_pdf_name':  "NFe%08d.pdf" % response['entity']['numero_nfe'],
            }
            if response.get('xml', False):
                vals['nfe_processada'] = base64.encodestring(response['xml'])
            if response.get('pdf', False):
                vals['nfse_pdf'] = base64.encodestring(response['pdf'])
            if response.get('url_nfe', False):
                vals['nfse_url'] = response['url_nfe']

            self.write(vals)

        elif response['code'] == 'processing':
            self.write({
                'state': 'processing',
            })
        else:
            raise UserError('%s - %s' %
                            (response['api_code'], response['message']))

    def action_check_status_nfse(self):
        for edoc in self:
            response = check_nfse_api(
                edoc.company_id.l10n_br_nfse_token_acess, 
                edoc.company_id.l10n_br_tipo_ambiente,
                str(edoc.id),
            )
            if response['code'] in (200, 201):
                vals = {
                    'protocolo_nfe': response['entity']['protocolo_nfe'],
                    'numero': response['entity']['numero_nfe'],
                    'state': 'done',
                    'codigo_retorno': '100',
                    'mensagem_retorno': 'Nota emitida com sucesso!',
                    'nfe_processada_name':  "NFe%08d.xml" % response['entity']['numero_nfe'],
                    'nfse_pdf_name':  "NFe%08d.pdf" % response['entity']['numero_nfe'],
                }
                if response.get('xml', False):
                    vals['nfe_processada'] = base64.encodestring(response['xml'])
                if response.get('pdf', False):
                    vals['nfse_pdf'] = base64.encodestring(response['pdf'])
                if response.get('url_nfe', False):
                    vals['nfse_url'] = response['url_nfe']
                edoc.write(vals)

            elif response['code'] == 400:
                edoc.write({
                    'state': 'error',
                    'codigo_retorno': response['api_code'],
                    'mensagem_retorno': response['message'],
                })


    def cron_check_status_nfse(self):
        documents = self.search([('state', '=', 'processing')], limit=100)
        documents.action_check_status_nfse()
        
    def action_cancel_document(self, context=None, justificativa=None):
        company = self.mapped('company_id').with_context({'bin_size': False})
        certificate = company.l10n_br_certificate
        password = company.l10n_br_cert_password
        doc_values = {
            'aedf': company.l10n_br_aedf,
            'client_id': company.l10n_br_client_id,
            'client_secret': company.l10n_br_client_secret,
            'user_password': company.l10n_br_user_password,
            'ambiente': self.ambiente,
            'cnpj_cpf': re.sub('[^0-9]', '', company.l10n_br_cnpj_cpf),
            'inscricao_municipal': re.sub('[^0-9]', '', company.l10n_br_inscr_mun),
            'justificativa': 'Emissao de nota fiscal errada',
            'numero': self.numero,
            'nfe_reference': str(self.id),
            'protocolo_nfe': self.protocolo_nfe,
            'codigo_municipio': '%s%s' % (
                company.state_id.l10n_br_ibge_code,
                company.city_id.l10n_br_ibge_code),
        }

        if doc_values['codigo_municipio'] == '4205407':
            from .nfse_florianopolis import cancel_api
            response = cancel_api(certificate, password, doc_values)
        elif doc_values['codigo_municipio'] == '3550308':
            from .nfse_paulistana import cancel_api
            response = cancel_api(certificate, password, doc_values)
        elif doc_values['codigo_municipio'] == '3106200':
            from .nfse_bh import cancel_api
            doc_values['inscricao_municipal'] = re.sub('\W+','', company.l10n_br_inscr_mun)
            doc_values['numero'] = str(self.data_emissao.year) + '{:>011d}'.format(self.numero)
            response = cancel_api(certificate, password, doc_values)
        else:
            from .focus_nfse import cancel_api
            response = cancel_api(
                company.l10n_br_nfse_token_acess,
                doc_values['ambiente'],
                doc_values['nfe_reference']
            )

        if response['code'] in (200, 201):
            vals = {
                'state': 'cancel',
                'codigo_retorno': response['code'],
                'mensagem_retorno': response['message']
            }
            if response.get('xml', False):
                # split na nfse antiga para adicionar o xml da nfe cancelada
                # [parte1 nfse] + [parte2 nfse]
                split_nfe_processada = base64.decodebytes(self.nfe_processada).split(b'</Nfse>')
                # readicionar a tag nfse pq o mesmo é removido ao dar split
                split_nfe_processada[0] = split_nfe_processada[0] + b'</Nfse>'
                # [parte1 nfse] + [parte2 nfse] + [parte2 nfse]
                split_nfe_processada.append(split_nfe_processada[1])
                # [parte1 nfse] + [nfse cancelada] + [parte2 nfse]
                split_nfe_processada[1] = response['xml']
                vals['nfe_processada'] = base64.encodebytes(b''.join(split_nfe_processada))
            self.write(vals)
        else:
            raise UserError('%s - %s' % (response['api_code'], response['message']))

    def qrcode_floripa_url(self):
        import urllib
        urlconsulta = "http://nfps-e.pmf.sc.gov.br/consulta-frontend/#!/\
consulta?cod=%s&cmc=%s" % (self.protocolo_nfe, self.company_id.l10n_br_inscr_mun)

        url = '<img class="center-block"\
style="max-width:100px;height:100px;margin:0px 0px;"src="/report/barcode/\
?type=QR&width=100&height=100&value=' + urllib.parse.quote(urlconsulta) + '"/>'
        return url

    def iss_due_date(self):
        next_month = self.data_emissao + relativedelta(months=1)
        due_date = date(next_month.year, next_month.month, 10)
        if due_date.weekday() >= 5:
            while due_date.weekday() != 0:
                due_date = due_date + timedelta(days=1)
        format = "%d/%m/%Y"
        due_date = datetime.strftime(due_date, format)
        return due_date


class EletronicDocumentLine(models.Model):
    _name = 'eletronic.document.line'
    _description = 'Eletronic document line (NFE, NFSe)'

    name = fields.Char(string='Name', size=30)
    eletronic_document_id = fields.Many2one(
        'eletronic.document', string='Documento')
    company_id = fields.Many2one(
        'res.company', 'Empresa', readonly=True, store=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency", store=True)

    state = fields.Selection(
        related='eletronic_document_id.state', string="State")

    product_id = fields.Many2one(
        'product.product', string='Produto', readonly=True, states=STATE)
    tipo_produto = fields.Selection(
        [('product', 'Produto'),
         ('service', 'Serviço')],
        string="Tipo Produto", readonly=True, states=STATE)
    cfop = fields.Char('CFOP', size=5, readonly=True, states=STATE)
    ncm = fields.Char('NCM', size=10, readonly=True, states=STATE)
    unidade_medida = fields.Char('Un. Medida Xml', size=10, readonly=True, states=STATE)

    item_lista_servico = fields.Char(
        string="Código do serviço", size=10, readonly=True, states=STATE)
    codigo_servico_municipio = fields.Char(
        string='Código NFSe', size=20, readonly=True, states=STATE)
    # Florianopolis
    codigo_cnae = fields.Char(string="CNAE", size=10,
                              readonly=True, states=STATE)
    # Paulistana
    codigo_servico_paulistana_nome = fields.Char(
        string='Descrição código NFSe Paulistana', readonly=True, states=STATE)

    uom_id = fields.Many2one(
        'uom.uom', string='Unidade Medida', readonly=True, states=STATE)
    quantidade = fields.Float(
        string='Quantidade', readonly=True, states=STATE,
        digits='Product Unit of Measure')
    preco_unitario = fields.Monetary(
        string='Preço Unitário', digits='Product Price',
        readonly=True, states=STATE)

    pedido_compra = fields.Char(
        string="Pedido Compra", size=60,
        help="Se setado aqui sobrescreve o pedido de compra da fatura")
    item_pedido_compra = fields.Char(
        string="Item de compra", size=20,
        help='Item do pedido de compra do cliente')

    frete = fields.Monetary(
        string='Frete', digits='Account',
        readonly=True, states=STATE)
    seguro = fields.Monetary(
        string='Seguro', digits='Account',
        readonly=True, states=STATE)
    desconto = fields.Monetary(
        string='Desconto', digits='Account',
        readonly=True, states=STATE)
    outras_despesas = fields.Monetary(
        string='Outras despesas', digits='Account',
        readonly=True, states=STATE)

    def _compute_tributos_estimados(self):
        for item in self:
            tributos_estimados = 0.0
            ncm = item.product_id.service_type_id if item.product_id.type == 'service' \
                else item.product_id.l10n_br_ncm_id
            if ncm:
                # origem nacional
                if item.product_id.l10n_br_origin in ['0', '3', '4', '5', '8']:
                    ncm_mult = (ncm.federal_nacional + ncm.estadual_imposto + ncm.municipal_imposto) / 100
                else:
                    ncm_mult = (ncm.federal_importado + ncm.estadual_imposto + ncm.municipal_imposto) / 100
                tributos_estimados += item.quantidade * item.preco_unitario * ncm_mult
            item.tributos_estimados = tributos_estimados

    tributos_estimados = fields.Monetary(
        string='Valor Estimado Tributos', digits='Account',
        readonly=True, states=STATE, compute="_compute_tributos_estimados")

    valor_bruto = fields.Monetary(
        string='Valor Bruto', digits='Account',
        readonly=True, states=STATE)
    valor_liquido = fields.Monetary(
        string='Valor Líquido', digits='Account',
        readonly=True, states=STATE)
    indicador_total = fields.Selection(
        [('0', '0 - Não'), ('1', '1 - Sim')],
        string="Compõe Total da Nota?", default='1',
        readonly=True, states=STATE)

    origem = fields.Selection(
        ORIGEM_PROD, string='Origem Mercadoria', readonly=True, states=STATE, default='0')
    icms_cst = fields.Selection(
        CST_ICMS + CSOSN_SIMPLES, string='Situação Tributária',
        readonly=True, states=STATE)
    icms_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    icms_tipo_base = fields.Selection(
        [('0', '0 - Margem Valor Agregado (%)'),
         ('1', '1 - Pauta (Valor)'),
         ('2', '2 - Preço Tabelado Máx. (valor)'),
         ('3', '3 - Valor da operação')],
        string='Modalidade BC do ICMS', readonly=True, states=STATE, default='3')
    icms_base_calculo = fields.Monetary(
        string='Base de cálculo', digits='Account',
        readonly=True, states=STATE)
    icms_aliquota_reducao_base = fields.Float(
        string='% Redução Base', digits='Account',
        readonly=True, states=STATE)
    icms_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)
    icms_valor_credito = fields.Monetary(
        string="Valor de Cŕedito", digits='Account',
        readonly=True, states=STATE)
    icms_aliquota_credito = fields.Float(
        string='% de Crédito', digits='Account',
        readonly=True, states=STATE)

    icms_st_tipo_base = fields.Selection(
        [('0', '0- Preço tabelado ou máximo  sugerido'),
         ('1', '1 - Lista Negativa (valor)'),
         ('2', '2 - Lista Positiva (valor)'),
         ('3', '3 - Lista Neutra (valor)'),
         ('4', '4 - Margem Valor Agregado (%)'), ('5', '5 - Pauta (valor)')],
        string='Tipo Base ICMS ST', required=True, default='4',
        readonly=True, states=STATE)
    icms_st_aliquota_mva = fields.Float(
        string='% MVA', digits='Account',
        readonly=True, states=STATE)
    icms_st_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    icms_st_base_calculo = fields.Monetary(
        string='Base de cálculo', digits='Account',
        readonly=True, states=STATE)
    icms_st_aliquota_reducao_base = fields.Float(
        string='% Redução Base', digits='Account',
        readonly=True, states=STATE)
    icms_st_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)

    icms_aliquota_diferimento = fields.Float(
        string='% Diferimento', digits='Account',
        readonly=True, states=STATE)
    icms_valor_diferido = fields.Monetary(
        string='Valor Diferido', digits='Account',
        readonly=True, states=STATE)

    icms_motivo_desoneracao = fields.Char(
        string='Motivo Desoneração', size=2, readonly=True, states=STATE)
    icms_valor_desonerado = fields.Monetary(
        string='Valor Desonerado', digits='Account',
        readonly=True, states=STATE)

    # ----------- IPI -------------------
    ipi_cst = fields.Selection(CST_IPI, string='Situação tributária')
    ipi_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    ipi_base_calculo = fields.Monetary(
        string='Base de cálculo', digits='Account',
        readonly=True, states=STATE)
    ipi_reducao_bc = fields.Float(
        string='% Redução Base', digits='Account',
        readonly=True, states=STATE)
    ipi_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)

    # ----------- II ----------------------
    ii_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    ii_aliquota = fields.Float(
        string='Alíquota II', digits='Account',
        readonly=True, states=STATE)
    ii_valor_despesas = fields.Monetary(
        string='Despesas Aduaneiras', digits='Account',
        readonly=True, states=STATE)
    ii_valor = fields.Monetary(
        string='Imposto de Importação', digits='Account',
        readonly=True, states=STATE)
    ii_valor_iof = fields.Monetary(
        string='IOF', digits='Account',
        readonly=True, states=STATE)

    # ------------ PIS ---------------------
    pis_cst = fields.Selection(
        CST_PIS_COFINS, string='Situação Tributária',
        readonly=True, states=STATE)
    pis_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    pis_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    pis_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)
    pis_valor_retencao = fields.Monetary(
        string='Valor Retido', digits='Account',
        readonly=True, states=STATE)

    # ------------ COFINS ------------
    cofins_cst = fields.Selection(
        CST_PIS_COFINS, string='Situação Tributária',
        readonly=True, states=STATE)
    cofins_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    cofins_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    cofins_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)
    cofins_valor_retencao = fields.Monetary(
        string='Valor Retido', digits='Account',
        readonly=True, states=STATE)

    # ----------- ISS -------------
    iss_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    iss_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    iss_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)
    iss_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)

    # ------------ RETENÇÔES ------------
    csll_base_calculo = fields.Monetary(
        string='Base CSLL', digits='Account',
        readonly=True, states=STATE)
    csll_aliquota = fields.Float(
        string='Alíquota CSLL', digits='Account',
        readonly=True, states=STATE)
    csll_valor = fields.Monetary(
        string='Valor CSLL', digits='Account',
        readonly=True, states=STATE)
    csll_valor_retencao = fields.Monetary(
        string='Retenção CSLL', digits='Account',
        readonly=True, states=STATE)
    irpj_base_calculo = fields.Monetary(
        string='Base IRPJ', digits='Account',
        readonly=True, states=STATE)
    irpj_aliquota = fields.Float(
        string='Alíquota IRPJ', digits='Account',
        readonly=True, states=STATE)
    irpj_valor = fields.Monetary(
        string='Valor IRPJ', digits='Account',
        readonly=True, states=STATE)
    irpj_valor_retencao = fields.Monetary(
        string='Retenção IRPJ', digits='Account',
        readonly=True, states=STATE)
    irrf_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    irrf_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    irrf_valor = fields.Monetary(
        string='Valor IRRF', digits='Account',
        readonly=True, states=STATE)
    irrf_valor_retencao = fields.Monetary(
        string='Retenção IRRF', digits='Account',
        readonly=True, states=STATE)
    inss_base_calculo = fields.Monetary(
        string='Base INSS', digits='Account',
        readonly=True, states=STATE)
    inss_aliquota = fields.Float(
        string='Alíquota INSS', digits='Account',
        readonly=True, states=STATE)
    inss_valor = fields.Monetary(
        string='Valor INSS', digits='Account',
        readonly=True, states=STATE)
    inss_valor_retencao = fields.Monetary(
        string='Retenção INSS', digits='Account',
        readonly=True, states=STATE)

    @api.depends('icms_cst', 'origem')
    def _compute_cst_danfe(self):
        for item in self:
            item.cst_danfe = (item.origem or '') + (item.icms_cst or '')

    cst_danfe = fields.Char(string="CST Danfe", compute="_compute_cst_danfe")

    cest = fields.Char(string="CEST", size=10, readonly=True, states=STATE,
                       help="Código Especificador da Substituição Tributária")
    classe_enquadramento_ipi = fields.Char(
        string="Classe Enquadramento", size=5, readonly=True, states=STATE)
    codigo_enquadramento_ipi = fields.Char(
        string="Classe Enquadramento", size=3, default='999',
        readonly=True, states=STATE)

    import_declaration_ids = fields.One2many(
        'nfe.import.declaration',
        'eletronic_document_line_id', string='Declaração de Importação')

    # ----------- ICMS INTERESTADUAL -----------
    tem_difal = fields.Boolean(string='Difal?', readonly=True, states=STATE)
    icms_bc_uf_dest = fields.Monetary(
        string=u'Base ICMS', readonly=True, states=STATE)
    icms_aliquota_fcp_uf_dest = fields.Float(
        string=u'% FCP', readonly=True, states=STATE)
    icms_aliquota_uf_dest = fields.Float(
        string=u'% ICMS destino', readonly=True, states=STATE)
    icms_aliquota_interestadual = fields.Float(
        string=u"% ICMS Inter", readonly=True, states=STATE)
    icms_aliquota_inter_part = fields.Float(
        string=u'% Partilha', default=100.0, readonly=True, states=STATE)
    icms_uf_remet = fields.Monetary(
        string=u'ICMS Remetente', readonly=True, states=STATE)
    icms_uf_dest = fields.Monetary(
        string=u'ICMS Destino', readonly=True, states=STATE)
    icms_fcp_uf_dest = fields.Monetary(
        string=u'Valor FCP', readonly=True, states=STATE)
    informacao_adicional = fields.Text(string=u"Informação Adicional")

    # =========================================================================
    # ICMS Retido anteriormente por ST
    # =========================================================================
    icms_substituto = fields.Monetary(
        "ICMS Substituto", readonly=True, states=STATE)
    icms_bc_st_retido = fields.Monetary(
        "Base Calc. ST Ret.", readonly=True, states=STATE)
    icms_aliquota_st_retido = fields.Float(
        "% ST Retido", readonly=True, states=STATE)
    icms_st_retido = fields.Monetary(
        "ICMS ST Ret.", readonly=True, states=STATE)