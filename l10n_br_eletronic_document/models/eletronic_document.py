import re
import json
import requests
from odoo import api, fields, models
from odoo.exceptions import UserError

from .cst import CST_ICMS, CST_PIS_COFINS, CSOSN_SIMPLES, CST_IPI, ORIGEM_PROD


STATE = {'edit': [('readonly', False)]}


class EletronicDocument(models.Model):
    _name = 'eletronic.document'
    _description = 'Eletronic documents (NFE, NFSe)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    code = fields.Char('Código', size=100, readonly=True, states=STATE)
    name = fields.Char(string='Name', size=30, readonly=True, states=STATE)
    company_id = fields.Many2one('res.company')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency", readonly=True, states=STATE)
    emission_date = fields.Datetime(
        string="Data de Emissão", readonly=True, states=STATE)
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
        'eletronic.document.line', 'eletronic_document_id', string="Linhas")

    # ------------ PIS ---------------------
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
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    csll_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)
    irrf_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    irrf_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)
    inss_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    inss_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)

    valor_final = fields.Monetary(
        string='Valor Final', readonly=True, states=STATE)

    state = fields.Selection(
        [('draft', u'Provisório'),
         ('edit', 'Editar'),
         ('error', 'Erro'),
         ('denied', 'Denegado'),
         ('done', 'Enviado'),
         ('cancel', 'Cancelado')],
        string=u'State', default='draft', readonly=True, states=STATE,
        track_visibility='always')
    schedule_user_id = fields.Many2one(
        'res.users', string="Agendado por", readonly=True,
        track_visibility='always')
    tipo_operacao = fields.Selection(
        [('entrada', 'Entrada'),
         ('saida', 'Saída')],
        string=u'Tipo de Operação', readonly=True, states=STATE)
    model = fields.Selection(
        [('55', u'55 - NFe'),
         ('65', u'65 - NFCe'),
         ('001', u'NFS-e - Nota Fiscal Paulistana'),
         ('002', u'NFS-e - Provedor GINFES'),
         ('008', u'NFS-e - Provedor SIMPLISS'),
         ('009', u'NFS-e - Provedor SUSESU'),
         ('010', u'NFS-e Imperial - Petrópolis'),
         ('012', u'NFS-e - Florianópolis')],
        string=u'Modelo', readonly=True, states=STATE)
    # serie = fields.Many2one(
    #     'br_account.document.serie', string=u'Série',
    #     readonly=True, states=STATE)
    serie_documento = fields.Char(string=u'Série Documento', size=6)
    numero = fields.Integer(
        string=u'Número', readonly=True, states=STATE)
    numero_controle = fields.Integer(
        string=u'Número de Controle', readonly=True, states=STATE)
    data_agendada = fields.Date(
        string=u'Data agendada',
        readonly=True,
        default=fields.Date.today,
        states=STATE)
    data_emissao = fields.Datetime(
        string=u'Data emissão', readonly=True, states=STATE)
    data_autorizacao = fields.Char(
        string=u'Data de autorização', size=30, readonly=True, states=STATE)
    ambiente = fields.Selection(
        [('homologacao', u'Homologação'),
         ('producao', u'Produção')],
        string=u'Ambiente', readonly=True, states=STATE)
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
    # eletronic_event_ids = fields.One2many(
    #     'invoice.eletronic.event', 'invoice_eletronic_id', string=u"Eventos",
    #     readonly=True, states=STATE)
    valor_bruto = fields.Monetary(
        string=u'Total Produtos', readonly=True, states=STATE)
    valor_frete = fields.Monetary(
        string=u'Total Frete', readonly=True, states=STATE)
    valor_seguro = fields.Monetary(
        string=u'Total Seguro', readonly=True, states=STATE)
    valor_desconto = fields.Monetary(
        string=u'Total Desconto', readonly=True, states=STATE)
    valor_despesas = fields.Monetary(
        string=u'Total Despesas', readonly=True, states=STATE)
    valor_bc_icms = fields.Monetary(
        string=u"Base de Cálculo ICMS", readonly=True, states=STATE)
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
    valor_pis = fields.Monetary(
        string=u"Total PIS", readonly=True, states=STATE)
    valor_cofins = fields.Monetary(
        string=u"Total COFINS", readonly=True, states=STATE)
    valor_estimado_tributos = fields.Monetary(
        string=u"Tributos Estimados", readonly=True, states=STATE)

    valor_servicos = fields.Monetary(
        string=u"Total Serviços", readonly=True, states=STATE)
    valor_bc_issqn = fields.Monetary(
        string=u"Base ISS", readonly=True, states=STATE)
    valor_issqn = fields.Monetary(
        string=u"Total ISS", readonly=True, states=STATE)
    valor_pis_servicos = fields.Monetary(
        string=u"Total PIS Serviços", readonly=True, states=STATE)
    valor_cofins_servicos = fields.Monetary(
        string=u"Total Cofins Serviço", readonly=True, states=STATE)

    informacoes_legais = fields.Text(
        string='Informações legais', readonly=True, states=STATE)
    informacoes_complementares = fields.Text(
        string='Informações complementares', readonly=True, states=STATE)

    codigo_retorno = fields.Char(
        string='Código Retorno', readonly=True, states=STATE,
        track_visibility='onchange')
    mensagem_retorno = fields.Char(
        string='Mensagem Retorno', readonly=True, states=STATE,
        track_visibility='onchange')
    numero_nfe = fields.Char(
        string="Numero Formatado NFe", readonly=True, states=STATE)

    xml_to_send = fields.Binary(string="Xml a Enviar", readonly=True)
    xml_to_send_name = fields.Char(
        string="Nome xml a ser enviado", size=100, readonly=True)

    email_sent = fields.Boolean(
        string="Email enviado", default=False, readonly=True, states=STATE)


    # payment_mode_id = fields.Many2one(
    #     'l10n_br.payment.mode', string='Modo de Pagamento',
    #     readonly=True, states=STATE)
    iest = fields.Char(string="IE Subst. Tributário")
    ambiente_nfe = fields.Selection(
        string=u"Ambiente NFe", related="company_id.l10n_br_tipo_ambiente",
        readonly=True)
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

    # reboque_ids = fields.One2many(
    #     'nfe.reboque', 'invoice_eletronic_id',
    #     string=u"Reboques", readonly=True, states=STATE)
    # volume_ids = fields.One2many(
    #     'nfe.volume', 'invoice_eletronic_id',
    #     string=u"Volumes", readonly=True, states=STATE)

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

    # duplicata_ids = fields.One2many(
    #     'nfe.duplicata', 'invoice_eletronic_id',
    #     string=u"Duplicatas", readonly=True, states=STATE)

    # Compras
    nota_empenho = fields.Char(
        string="Nota de Empenho", size=22, readonly=True, states=STATE)
    pedido_compra = fields.Char(
        string="Pedido Compra", size=60, readonly=True, states=STATE)
    contrato_compra = fields.Char(
        string="Contrato Compra", size=60, readonly=True, states=STATE)

    sequencial_evento = fields.Integer(
        string=u"Sequêncial Evento", default=1, readonly=True, states=STATE)
    recibo_nfe = fields.Char(
        string=u"Recibo NFe", size=50, readonly=True, states=STATE)
    chave_nfe = fields.Char(
        string=u"Chave NFe", size=50, readonly=True, states=STATE)
    chave_nfe_danfe = fields.Char(
        string=u"Chave Formatado", compute="_compute_format_danfe_key")
    protocolo_nfe = fields.Char(
        string=u"Protocolo", size=50, readonly=True, states=STATE,
        help=u"Protocolo de autorização da NFe")
    nfe_processada = fields.Binary(string=u"Xml da NFe", readonly=True)
    nfe_processada_name = fields.Char(
        string=u"Xml da NFe", size=100, readonly=True)

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

    def generate_dict_values(self):
        dict_docs = []
        for doc in self:
            partner = doc.partner_id

            emissor = {
                'cnpj': re.sub('[^0-9]', '', doc.company_id.l10n_br_cnpj_cpf or ''),
                'inscricao_municipal': re.sub('[^0-9]', '', doc.company_id.l10n_br_inscr_mun or ''),
                'codigo_municipio': '%s%s' % (
                    doc.company_id.state_id.l10n_br_ibge_code,
                    doc.company_id.city_id.l10n_br_ibge_code),
            }
            tomador = {
                'cpf': re.sub(
                    '[^0-9]', '', partner.l10n_br_cnpj_cpf or ''),
                'inscricao_municipal': re.sub(
                    '[^0-9]', '', partner.l10n_br_inscr_mun or
                    '0000000'),
                'razao_social': partner.l10n_br_legal_name or partner.name,
                'telefone': re.sub('[^0-9]', '', self.partner_id.phone or ''),
                'email': self.partner_id.email,
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
                aliquota = line.issqn_aliquota / 100
                base = line.issqn_base_calculo
                unitario = round(line.valor_liquido / line.quantidade, 2)
                items.append({
                    'name': line.product_id.name,
                    'cnae': re.sub(
                        '[^0-9]', '',
                        line.product_id.service_type_id.id_cnae or ''),
                    'cst_servico': '1',
                    'aliquota': aliquota,
                    'base_calculo': base,
                    'valor_unitario': unitario,
                    'quantidade': int(line.quantidade),
                    'valor_total': line.valor_liquido,
                })
            emissao = fields.Datetime.from_string(doc.emission_date)
            outra_cidade = doc.company_id.city_id.id != partner.city_id.id
            outro_estado = doc.company_id.state_id.id != partner.state_id.id
            outro_pais = doc.company_id.country_id.id != partner.country_id.id

            data = {
                'ambiente': 'homologacao',
                'emissor': emissor,
                'tomador': tomador,
                'numero': "%06d" % doc.identifier,
                'outra_cidade': outra_cidade,
                'outro_estado': outro_estado,
                'outro_pais': outro_pais,
                'regime_tributario': doc.company_id.l10n_br_tax_regime,
                'itens_servico': items,
                'data_emissao': emissao.strftime('%Y-%m-%d'),
                'base_calculo': doc.iss_base_calculo,
                'valor_iss': doc.iss_valor,
                'valor_total': doc.valor_final,

                'aedf': doc.company_id.l10n_br_aedf,
                'client_id': doc.company_id.l10n_br_client_id,
                'client_secret': doc.company_id.l10n_br_client_secret,
                'user_password': doc.company_id.l10n_br_user_password,
                'observacoes': '',
            }
            dict_docs.append(data)
        return dict_docs

    def generate(self):
        company = self.mapped('company_id').with_context({'bin_size': False})

        certificate = company.l10n_br_certificate
        password = company.l10n_br_cert_password
        doc_values = self.generate_dict_values()

        response = {}
        if doc_values[0]['emissor']['codigo_municipio'] == '4205407':
            from .nfse_florianopolis import send_api
            response = send_api(certificate, password, doc_values)
        elif doc_values[0]['emissor']['codigo_municipio'] == '3550308':
            from .nfse_paulistana import send_api
            response = send_api(certificate, password, doc_values)
        else:
            from .focus_nfse import send_api
            response = send_api(certificate, password, doc_values)

        if response['code'] in (200, 201):
            print(response)
        else:
            raise UserError('%s - %s' %
                            (response['api_code'], response['message']))


class EletronicDocumentLine(models.Model):
    _name = 'eletronic.document.line'
    _description = 'Eletronic document line (NFE, NFSe)'

    name = fields.Char(string='Name', size=30)
    company_id = fields.Many2one(
        'res.company', 'Empresa')
    eletronic_document_id = fields.Many2one(
        'eletronic.document', string='Documento')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency")

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

    tributos_estimados = fields.Monetary(
        string='Valor Estimado Tributos', digits='Account',
        readonly=True, states=STATE)

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
        ORIGEM_PROD, string='Origem Mercadoria', readonly=True, states=STATE)
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
        string='Modalidade BC do ICMS', readonly=True, states=STATE)
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

    # ----------- ISSQN -------------
    issqn_codigo = fields.Char(
        string='Código', size=10, readonly=True, states=STATE)
    issqn_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    issqn_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    issqn_valor = fields.Monetary(
        string='Valor Total', digits='Account',
        readonly=True, states=STATE)
    issqn_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)

    # ------------ RETENÇÔES ------------
    csll_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    csll_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    csll_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)
    irrf_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    irrf_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    irrf_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)
    inss_base_calculo = fields.Monetary(
        string='Base de Cálculo', digits='Account',
        readonly=True, states=STATE)
    inss_aliquota = fields.Float(
        string='Alíquota', digits='Account',
        readonly=True, states=STATE)
    inss_valor_retencao = fields.Monetary(
        string='Valor Retenção', digits='Account',
        readonly=True, states=STATE)
