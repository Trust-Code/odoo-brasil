# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import base64
import copy
import logging
from datetime import datetime, timedelta
import dateutil.relativedelta as relativedelta
from odoo.exceptions import UserError
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.addons.br_account.models.cst import CST_ICMS
from odoo.addons.br_account.models.cst import CSOSN_SIMPLES
from odoo.addons.br_account.models.cst import CST_IPI
from odoo.addons.br_account.models.cst import CST_PIS_COFINS
from odoo.addons.br_account.models.cst import ORIGEM_PROD
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

_logger = logging.getLogger(__name__)

STATE = {'edit': [('readonly', False)]}


# format_amount function for fiscal observation
# This way we can format numbers in currency template on fiscal observation msg
# We'll call this function when setting the variables env below
def format_amount(env, amount, currency):
    fmt = "%.{0}f".format(currency.decimal_places)
    lang = env['res.lang']._lang_get(env.context.get('lang') or 'en_US')

    formatted_amount = lang.format(
        fmt, currency.round(amount), grouping=True, monetary=True).replace(
            r' ', u'\N{NO-BREAK SPACE}').replace(
                r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

    pre = post = u''
    if currency.position == 'before':
        pre = u'{symbol}\N{NO-BREAK SPACE}'.format(
            symbol=currency.symbol or '')
    else:
        post = u'\N{NO-BREAK SPACE}{symbol}'.format(
            symbol=currency.symbol or '')

    return u'{pre}{0}{post}'.format(formatted_amount, pre=pre, post=post)


class InvoiceEletronic(models.Model):
    _name = 'invoice.eletronic'
    _description = "Nota Fiscal"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    code = fields.Char(
        u'Código', size=100, required=True, readonly=True, states=STATE)
    name = fields.Char(
        u'Nome', size=100, required=True, readonly=True, states=STATE)
    company_id = fields.Many2one(
        'res.company', u'Empresa', readonly=True, states=STATE)
    state = fields.Selection(
        [('draft', u'Provisório'),
         ('edit', 'Editar'),
         ('error', 'Erro'),
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
    serie = fields.Many2one(
        'br_account.document.serie', string=u'Série',
        readonly=True, states=STATE)
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
    invoice_id = fields.Many2one(
        'account.invoice', string=u'Fatura', readonly=True, states=STATE)
    partner_id = fields.Many2one(
        'res.partner', string=u'Parceiro', readonly=True, states=STATE)
    commercial_partner_id = fields.Many2one(
        'res.partner', string='Commercial Entity',
        related='partner_id.commercial_partner_id', store=True)
    partner_shipping_id = fields.Many2one(
        'res.partner', string=u'Entrega', readonly=True, states=STATE)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Condição pagamento',
        readonly=True, states=STATE)
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string=u'Posição Fiscal',
        readonly=True, states=STATE)
    eletronic_item_ids = fields.One2many(
        'invoice.eletronic.item', 'invoice_eletronic_id', string=u"Linhas",
        readonly=True, states=STATE)
    eletronic_event_ids = fields.One2many(
        'invoice.eletronic.event', 'invoice_eletronic_id', string=u"Eventos",
        readonly=True, states=STATE)
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

    valor_retencao_issqn = fields.Monetary(
        string=u"Retenção ISSQN", readonly=True, states=STATE)
    valor_retencao_pis = fields.Monetary(
        string=u"Retenção PIS", readonly=True, states=STATE)
    valor_retencao_cofins = fields.Monetary(
        string=u"Retenção COFINS", readonly=True, states=STATE)
    valor_bc_irrf = fields.Monetary(
        string=u"Base de Cálculo IRRF", readonly=True, states=STATE)
    valor_retencao_irrf = fields.Monetary(
        string=u"Retenção IRRF", readonly=True, states=STATE)
    valor_bc_csll = fields.Monetary(
        string=u"Base de Cálculo CSLL", readonly=True, states=STATE)
    valor_retencao_csll = fields.Monetary(
        string=u"Retenção CSLL", readonly=True, states=STATE)
    valor_bc_inss = fields.Monetary(
        string=u"Base de Cálculo INSS", readonly=True, states=STATE)
    valor_retencao_inss = fields.Monetary(
        string=u"Retenção INSS", help=u"Retenção Previdência Social",
        readonly=True, states=STATE)

    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency")
    valor_final = fields.Monetary(
        string=u'Valor Final', readonly=True, states=STATE)

    informacoes_legais = fields.Text(
        string=u'Informações legais', readonly=True, states=STATE)
    informacoes_complementares = fields.Text(
        string=u'Informações complementares', readonly=True, states=STATE)

    codigo_retorno = fields.Char(
        string=u'Código Retorno', readonly=True, states=STATE,
        track_visibility='onchange')
    mensagem_retorno = fields.Char(
        string=u'Mensagem Retorno', readonly=True, states=STATE,
        track_visibility='onchange')
    numero_nfe = fields.Char(
        string=u"Numero Formatado NFe", readonly=True, states=STATE)

    xml_to_send = fields.Binary(string="Xml a Enviar", readonly=True)
    xml_to_send_name = fields.Char(
        string=u"Nome xml a ser enviado", size=100, readonly=True)

    email_sent = fields.Boolean(string=u"Email enviado", default=False,
                                readonly=True, states=STATE)

    def _create_attachment(self, prefix, event, data):
        file_name = '%s-%s.xml' % (
            prefix, datetime.now().strftime('%Y-%m-%d-%H-%M'))
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(data.encode()),
                'datas_fname': file_name,
                'description': u'',
                'res_model': 'invoice.eletronic',
                'res_id': event.id
            })

    @api.multi
    def _hook_validation(self):
        """
            Override this method to implement the validations specific
            for the city you need
            @returns list<string> errors
        """
        errors = []
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
        if not self.company_id.partner_id.zip or len(
                re.sub(r"\D", "", self.company_id.partner_id.zip)) != 8:
            errors.append(u'Emitente / Endereço - CEP')
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

        # produtos
        for eletr in self.eletronic_item_ids:
            if eletr.product_id:
                if not eletr.product_id.default_code:
                    errors.append(
                        u'Prod: %s - Código do produto' % (
                            eletr.product_id.name))

        partner = self.partner_id.commercial_partner_id
        if not partner:  # NFC-e pode não ter partner, mas se tiver valida
            return errors
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
            if not partner.zip or len(
                    re.sub(r"\D", "", partner.zip)) != 8:
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
        return errors

    @api.multi
    def _compute_legal_information(self):
        fiscal_ids = self.invoice_id.fiscal_observation_ids.filtered(
            lambda x: x.tipo == 'fiscal')
        obs_ids = self.invoice_id.fiscal_observation_ids.filtered(
            lambda x: x.tipo == 'observacao')

        prod_obs_ids = self.env['br_account.fiscal.observation'].browse()
        for item in self.invoice_id.invoice_line_ids:
            prod_obs_ids |= item.product_id.fiscal_observation_ids

        fiscal_ids |= prod_obs_ids.filtered(lambda x: x.tipo == 'fiscal')
        obs_ids |= prod_obs_ids.filtered(lambda x: x.tipo == 'observacao')

        fiscal = self._compute_msg(fiscal_ids) + (
            self.invoice_id.fiscal_comment or '')
        observacao = self._compute_msg(obs_ids) + (
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
            'relativedelta': lambda *a, **kw: relativedelta.relativedelta(
                *a, **kw),
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
            'invoice': self.invoice_id
            }

    @api.multi
    def validate_invoice(self):
        self.ensure_one()
        errors = self._hook_validation()
        if len(errors) > 0:
            msg = u"\n".join(
                [u"Por favor corrija os erros antes de prosseguir"] + errors)
            self.sudo().unlink()
            raise UserError(msg)

    @api.multi
    def action_post_validate(self):
        self._compute_legal_information()

    @api.multi
    def _prepare_eletronic_invoice_item(self, item, invoice):
        return {}

    @api.multi
    def _prepare_eletronic_invoice_values(self):
        return {}

    @api.multi
    def action_send_eletronic_invoice(self):
        pass

    @api.multi
    def action_cancel_document(self, context=None, justificativa=None):
        pass

    @api.multi
    def action_back_to_draft(self):
        self.action_post_validate()
        self.state = 'draft'

    @api.multi
    def action_edit_edoc(self):
        self.state = 'edit'

    def can_unlink(self):
        if self.state not in ('done', 'cancel'):
            return True
        return False

    @api.multi
    def unlink(self):
        for item in self:
            if not item.can_unlink():
                raise UserError(
                    _('Documento Eletrônico enviado - Proibido excluir'))
        super(InvoiceEletronic, self).unlink()

    def log_exception(self, exc):
        self.codigo_retorno = -1
        self.mensagem_retorno = str(exc)

    def notify_user(self):
        msg = _('Verifique a %s, ocorreu um problema com o envio de \
                documento eletrônico!') % self.name
        self.create_uid.notify_warning(
            msg, sticky=True, title="Ação necessária!")
        try:
            activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
        except ValueError:
            activity_type_id = False
        self.env['mail.activity'].create({
            'activity_type_id': activity_type_id,
            'note': _('Please verify the eletronic document'),
            'user_id': self.schedule_user_id.id,
            'res_id': self.id,
            'res_model_id': self.env.ref(
                'br_account_einvoice.model_invoice_eletronic').id,
        })

    def _get_state_to_send(self):
        return ('draft',)

    @api.multi
    def cron_send_nfe(self, limit=50):
        inv_obj = self.env['invoice.eletronic'].with_context({
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
                self.env.cr.commit()
            except Exception as e:
                item.log_exception(e)
                item.notify_user()
                _logger.error(
                    'Erro no envio de documento eletrônico', exc_info=True)

    def _find_attachment_ids_email(self):
        return []

    @api.multi
    def send_email_nfe(self):
        mail = self.env.user.company_id.nfe_email_template
        if not mail:
            raise UserError(_('Modelo de email padrão não configurado'))
        atts = self._find_attachment_ids_email()
        _logger.info('Sending e-mail for e-doc %s (number: %s)' % (
            self.id, self.numero))

        values = mail.generate_email([self.invoice_id.id])[self.invoice_id.id]
        subject = values.pop('subject')
        values.pop('body')
        values.pop('attachment_ids')
        # Hack - Those attachments are being encoded twice,
        # so lets decode to message_post encode again
        new_items = []
        for item in values.get('attachments', []):
            new_items.append((item[0], base64.b64decode(item[1])))
        values['attachments'] = new_items
        self.invoice_id.message_post(
            body=values['body_html'], subject=subject,
            message_type='email', subtype='mt_comment',
            attachment_ids=atts + mail.attachment_ids.ids, **values)

    @api.multi
    def send_email_nfe_queue(self):
        after = datetime.now() + timedelta(days=-1)
        nfe_queue = self.env['invoice.eletronic'].search(
            [('data_emissao', '>=', after.strftime(DATETIME_FORMAT)),
             ('email_sent', '=', False),
             ('state', '=', 'done')], limit=5)
        for nfe in nfe_queue:
            nfe.send_email_nfe()
            nfe.email_sent = True

    @api.multi
    def copy(self, default=None):
        raise UserError(_('Não é possível duplicar uma Nota Fiscal.'))


class InvoiceEletronicEvent(models.Model):
    _name = 'invoice.eletronic.event'
    _description = "Eventos de nota fiscal eletrônica"
    _order = 'id desc'

    code = fields.Char(string=u'Código', readonly=True, states=STATE)
    name = fields.Char(string=u'Mensagem', readonly=True, states=STATE)
    invoice_eletronic_id = fields.Many2one(
        'invoice.eletronic', string=u"Fatura Eletrônica",
        readonly=True, states=STATE)
    state = fields.Selection(
        related='invoice_eletronic_id.state', string="State")


class InvoiceEletronicItem(models.Model):
    _name = 'invoice.eletronic.item'
    _description = "Item da nota fiscal eletrônica"

    name = fields.Text(u'Nome', readonly=True, states=STATE)
    company_id = fields.Many2one(
        'res.company', u'Empresa', index=True, readonly=True, states=STATE)
    invoice_eletronic_id = fields.Many2one(
        'invoice.eletronic', string=u'Documento', readonly=True, states=STATE)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company Currency")
    state = fields.Selection(
        related='invoice_eletronic_id.state', string="State")

    product_id = fields.Many2one(
        'product.product', string=u'Produto', readonly=True, states=STATE)
    tipo_produto = fields.Selection(
        [('product', 'Produto'),
         ('service', u'Serviço')],
        string="Tipo Produto", readonly=True, states=STATE)
    cfop = fields.Char(u'CFOP', size=5, readonly=True, states=STATE)
    ncm = fields.Char(u'NCM', size=10, readonly=True, states=STATE)

    uom_id = fields.Many2one(
        'uom.uom', string=u'Unidade Medida', readonly=True, states=STATE)
    quantidade = fields.Float(
        string=u'Quantidade', readonly=True, states=STATE,
        digits=dp.get_precision('Product Unit of Measure'))
    preco_unitario = fields.Monetary(
        string=u'Preço Unitário', digits=dp.get_precision('Product Price'),
        readonly=True, states=STATE)

    pedido_compra = fields.Char(
        string="Pedido Compra", size=60,
        help="Se setado aqui sobrescreve o pedido de compra da fatura")
    item_pedido_compra = fields.Char(
        string="Item de compra", size=20,
        help=u'Item do pedido de compra do cliente')

    frete = fields.Monetary(
        string=u'Frete', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    seguro = fields.Monetary(
        string=u'Seguro', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    desconto = fields.Monetary(
        string=u'Desconto', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    outras_despesas = fields.Monetary(
        string=u'Outras despesas', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    tributos_estimados = fields.Monetary(
        string=u'Valor Estimado Tributos', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    valor_bruto = fields.Monetary(
        string=u'Valor Bruto', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    valor_liquido = fields.Monetary(
        string=u'Valor Líquido', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    indicador_total = fields.Selection(
        [('0', u'0 - Não'), ('1', u'1 - Sim')],
        string=u"Compõe Total da Nota?", default='1',
        readonly=True, states=STATE)

    origem = fields.Selection(
        ORIGEM_PROD, string=u'Origem Mercadoria', readonly=True, states=STATE)
    icms_cst = fields.Selection(
        CST_ICMS + CSOSN_SIMPLES, string=u'Situação Tributária',
        readonly=True, states=STATE)
    icms_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_tipo_base = fields.Selection(
        [('0', u'0 - Margem Valor Agregado (%)'),
         ('1', u'1 - Pauta (Valor)'),
         ('2', u'2 - Preço Tabelado Máx. (valor)'),
         ('3', u'3 - Valor da operação')],
        string=u'Modalidade BC do ICMS', readonly=True, states=STATE)
    icms_base_calculo = fields.Monetary(
        string=u'Base de cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_aliquota_reducao_base = fields.Float(
        string=u'% Redução Base', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_valor_credito = fields.Monetary(
        string=u"Valor de Cŕedito", digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_aliquota_credito = fields.Float(
        string=u'% de Crédito', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    icms_st_tipo_base = fields.Selection(
        [('0', u'0- Preço tabelado ou máximo  sugerido'),
         ('1', u'1 - Lista Negativa (valor)'),
         ('2', u'2 - Lista Positiva (valor)'),
         ('3', u'3 - Lista Neutra (valor)'),
         ('4', u'4 - Margem Valor Agregado (%)'), ('5', '5 - Pauta (valor)')],
        string='Tipo Base ICMS ST', required=True, default='4',
        readonly=True, states=STATE)
    icms_st_aliquota_mva = fields.Float(
        string=u'% MVA', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_st_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_st_base_calculo = fields.Monetary(
        string=u'Base de cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_st_aliquota_reducao_base = fields.Float(
        string=u'% Redução Base', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_st_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    icms_aliquota_diferimento = fields.Float(
        string=u'% Diferimento', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    icms_valor_diferido = fields.Monetary(
        string=u'Valor Diferido', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    icms_motivo_desoneracao = fields.Char(
        string=u'Motivo Desoneração', size=2, readonly=True, states=STATE)
    icms_valor_desonerado = fields.Monetary(
        string=u'Valor Desonerado', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ----------- IPI -------------------
    ipi_cst = fields.Selection(CST_IPI, string=u'Situação tributária')
    ipi_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ipi_base_calculo = fields.Monetary(
        string=u'Base de cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ipi_reducao_bc = fields.Float(
        string=u'% Redução Base', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ipi_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ----------- II ----------------------
    ii_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ii_aliquota = fields.Float(
        string=u'Alíquota II', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ii_valor_despesas = fields.Monetary(
        string=u'Despesas Aduaneiras', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ii_valor = fields.Monetary(
        string=u'Imposto de Importação', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    ii_valor_iof = fields.Monetary(
        string=u'IOF', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ------------ PIS ---------------------
    pis_cst = fields.Selection(
        CST_PIS_COFINS, string=u'Situação Tributária',
        readonly=True, states=STATE)
    pis_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    pis_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    pis_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    pis_valor_retencao = fields.Monetary(
        string=u'Valor Retido', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ------------ COFINS ------------
    cofins_cst = fields.Selection(
        CST_PIS_COFINS, string=u'Situação Tributária',
        readonly=True, states=STATE)
    cofins_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    cofins_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    cofins_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    cofins_valor_retencao = fields.Monetary(
        string=u'Valor Retido', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ----------- ISSQN -------------
    issqn_codigo = fields.Char(
        string=u'Código', size=10, readonly=True, states=STATE)
    issqn_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    issqn_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    issqn_valor = fields.Monetary(
        string=u'Valor Total', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    issqn_valor_retencao = fields.Monetary(
        string=u'Valor Retenção', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    # ------------ RETENÇÔES ------------
    csll_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    csll_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    csll_valor_retencao = fields.Monetary(
        string=u'Valor Retenção', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    irrf_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    irrf_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    irrf_valor_retencao = fields.Monetary(
        string=u'Valor Retenção', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    inss_base_calculo = fields.Monetary(
        string=u'Base de Cálculo', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    inss_aliquota = fields.Float(
        string=u'Alíquota', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)
    inss_valor_retencao = fields.Monetary(
        string=u'Valor Retenção', digits=dp.get_precision('Account'),
        readonly=True, states=STATE)

    account_invoice_line_id = fields.Many2one(
        string="Account Invoice Line",
        comodel_name="account.invoice.line",
        )
