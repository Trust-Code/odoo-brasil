import base64
from datetime import datetime
from odoo import models, api, fields
from odoo.exceptions import ValidationError, UserError
from ..service.mde import exec_download_nfe, send_event
import gzip
import io
from lxml import objectify


def convert(obj, conversion=None):
    if conversion:
        return conversion(obj)
    if isinstance(obj, objectify.StringElement):
        return str(obj)
    if isinstance(obj, objectify.IntElement):
        return int(obj)
    if isinstance(obj, objectify.FloatElement):
        return float(obj)
    raise u"Tipo não implementado %s" % str(type(obj))


def get(obj, path, conversion=None):
    paths = path.split(".")
    index = 0
    for item in paths:
        if hasattr(obj, item):
            obj = obj[item]
            index += 1
        else:
            return None
    if len(paths) == index:
        return convert(obj, conversion=conversion)
    return None


def cnpj_cpf_format(cnpj_cpf):
    if len(cnpj_cpf) == 14:
        cnpj_cpf = (cnpj_cpf[0:2] + '.' + cnpj_cpf[2:5] +
                    '.' + cnpj_cpf[5:8] +
                    '/' + cnpj_cpf[8:12] +
                    '-' + cnpj_cpf[12:14])
    else:
        cnpj_cpf = (cnpj_cpf[0:3] + '.' + cnpj_cpf[3:6] +
                    '.' + cnpj_cpf[6:9] + '-' + cnpj_cpf[9:11])
    return cnpj_cpf


class NfeMde(models.Model):
    _name = 'nfe.mde'
    _description = "Manifesto de NFe"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'mail.bot']
    _rec_name = 'numero_sequencial'
    _order = 'numero_sequencial desc'

    def name_get(self):
        return [(rec.id,
                 u"NFº: {0} ({1}): {2}".format(
                     rec.numero_nfe, rec.cnpj_fornecedor, rec.razao_social)
                 ) for rec in self]

    def _default_company(self):
        return self.env.company

    def _compute_total_edocs(self):
        for item in self:
            item.total_edocs = self.env['eletronic.document'].search_count(
                [('nfe_mde_id', '=', item.id)])

    company_id = fields.Many2one('res.company', string=u"Empresa",
                                 default=_default_company, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  string=u'Moeda', readonly=True)
    chave_nfe = fields.Char(string=u"Chave de Acesso", size=50, readonly=True)
    numero_nfe = fields.Char(string=u"Número NFe", size=10, readonly=True)
    numero_sequencial = fields.Char(
        string=u"Número Sequencial", readonly=True, size=20)
    cnpj_fornecedor = fields.Char(string=u"CNPJ", readonly=True, size=20)
    inscricao_estadual = fields.Char(string=u"RG/IE", readonly=True, size=20)
    razao_social = fields.Char(string=u"Razão Social", readonly=True, size=200)
    partner_id = fields.Many2one('res.partner', string=u'Fornecedor')
    data_emissao = fields.Datetime(string=u"Data Emissão", readonly=True)
    tipo_operacao = fields.Selection(
        [('0', 'Entrada'), ('1', 'Saída')],
        string=u"Tipo de Operação", readonly=True)
    valor_nfe = fields.Float(
        string=u"Valor Total da NF-e", readonly=True, digits=(18, 2))
    situacao_nfe = fields.Selection(
        [('1', 'Autorizada'), ('2', 'Cancelada'), ('3', 'Denegada')],
        string=u"Situação da NF-e", readonly=True)
    state = fields.Selection(string=u"Situação da Manifestação", readonly=True,
                             selection=[
                                 ('pending', 'Pendente'),
                                 ('ciente', 'Ciente da operação'),
                                 ('confirmado', 'Confirmada operação'),
                                 ('desconhecido', 'Desconhecimento'),
                                 ('nao_realizado', 'Não realizado')
                             ])
    forma_inclusao = fields.Char(string=u"Forma de Inclusão", readonly=True)
    data_inclusao = fields.Datetime(string=u"Data de Inclusão", readonly=True)
    # eletronic_event_ids = fields.One2many(
    #     'invoice.eletronic.event', 'nfe_mde_id', string=u"Eventos",
    #     readonly=True)
    nfe_processada = fields.Binary(string=u"Xml da NFe", readonly=True)
    nfe_processada_name = fields.Char(
        string="Nome Xml da NFe", size=100, readonly=True)
    is_processed = fields.Boolean(string="Processado?", default=False)
    is_imported = fields.Boolean(string="Importado?", default=False)
    total_edocs = fields.Integer(string="Total NFe",
                                 compute=_compute_total_edocs)

    @api.constrains('cnpj_fornecedor', 'partner_id')
    def _check_partner_id(self):
        if self.partner_id and \
           self.cnpj_fornecedor != self.partner_id.l10n_br_cnpj_cpf:
            raise ValidationError(
                u"O Parceiro não possui o mesmo CNPJ/CPF do manifesto atual")

    def action_view_edocs(self):
        if self.total_edocs == 1:
            _, view_id = self.env['ir.model.data']._xmlid_to_res_model_res_id(
                'l10n_br_eletronic_document.view_eletronic_document_form')
            vals = self.env['ir.actions.act_window']._for_xml_id('l10n_br_eletronic_document.action_view_eletronic_document')
            vals['view_id'] = (view_id, 'sped.eletronic.doc.form')
            vals['views'][1] = (view_id, 'form')
            vals['views'] = [vals['views'][1], vals['views'][0]]
            edoc = self.env['eletronic.document'].search(
                [('nfe_mde_id', '=', self.id)], limit=1)
            vals['res_id'] = edoc.id
            return vals
        else:
            vals = self.env['ir.actions.act_window']._for_xml_id('l10n_br_eletronic_document.action_view_eletronic_document')
            return vals

    def _needaction_domain_get(self):
        return [('state', '=', 'pending')]

    def _create_event(self, code, message, mde_id):
        return {
            'code': code,
            'name': message,
            'nfe_mde_id': mde_id
        }

    def _create_attachment(self, event, result):
        file_name = 'evento-manifesto-%s.xml' % datetime.now().strftime(
            '%Y-%m-%d-%H-%M')
        self.env['ir.attachment'].create(
            {
                'name': file_name,
                'datas': base64.b64encode(result['file_returned']),
                'description': 'Evento Manifesto Destinatário',
                'res_model': 'l10n_br_account.document_event',
                'res_id': event.id
            })

    def action_known_emission(self):
        if self.state != 'pending':
            return True
        evento = {
            'tpEvento': 210210,
            'descEvento': 'Ciencia da Operacao',
        }

        nfe_result = send_event(
            self.company_id, self.chave_nfe, 'ciencia_operacao', self.id,
            evento=evento)

        if nfe_result['code'] == 135:
            self.state = 'ciente'
        elif nfe_result['code'] == 573:
            self.state = 'ciente'
            self.message_post(body='Ciência da operação já previamente realizada')
        else:
            self.message_post(
                body='Download do xml não foi possível: %s - %s' % (
                    nfe_result['code'], nfe_result['message']
                    ))
            return False

        return True

    def action_confirm_operation(self):
        evento = {
            'tpEvento': 210200,
            'descEvento': u'Confirmacao da Operacao',
        }
        nfe_result = send_event(
            self.company_id, self.chave_nfe, 'confirma_operacao', self.id,
            evento=evento)

        if nfe_result['code'] == 135:
            self.state = 'confirmado'
        elif nfe_result['code'] == 573:
            self.state = 'confirmado'
            self.message_post(body='Confirmação da operação já previamente realizada')

        return True

    def action_unknown_operation(self):
        evento = {
            'tpEvento': 210220,
            'descEvento': u'Desconhecimento da Operacao',
        }
        nfe_result = send_event(
            self.company_id, self.chave_nfe, 'desconhece_operacao',
            self.id, evento=evento)

        if nfe_result['code'] == 135:
            self.state = 'desconhecido'
        elif nfe_result['code'] == 573:
            self.state = 'desconhecido'
            self.message_post(body='Desconhecimento da operação já previamente realizado')

        return True

    def action_not_operation(self, context=None, justificativa=None):
        evento = {
            'tpEvento': 210240,
            'descEvento': u'Operacao nao Realizada',
        }

        if not justificativa:
            return {
                'name': 'Operação Não Realizada',
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.operation.not.perfomed',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_mde_id': self.id
                }
            }

        nfe_result = send_event(
            self.company_id, self.chave_nfe, 'nao_realizar_operacao',
            self.id, evento=evento, justificativa=justificativa)

        if nfe_result['code'] == 135:
            self.state = 'nao_realizado'
        elif nfe_result['code'] == 573:
            self.state = 'nao_realizado'
            self.message_post(body='Tentativa de Operação não realizada ja previamente realizada')

        return True

    def action_download_xml(self):
        nfe_result = exec_download_nfe(self.company_id, [self.chave_nfe])
        if nfe_result['code'] == 138:
            file_name = 'NFe%08d.xml' % int(self.chave_nfe[25:34])

            retorno = nfe_result['object']
            orig_file_desc = gzip.GzipFile(
                mode='r',
                fileobj=io.BytesIO(
                    base64.b64decode(str(retorno.loteDistDFeInt.docZip)))
            )

            orig_file_cont = orig_file_desc.read()
            orig_file_desc.close()

            if orig_file_cont:
                self.write({
                    'nfe_processada': base64.encodestring(orig_file_cont),
                    'nfe_processada_name': file_name,
                })
                return True
            else:
                self.message_post(
                    body='Download do xml não foi possível - Erro desconhecido')
        else:
            self.message_post(
                body='Download do xml não foi possível: %s - %s' % (
                    nfe_result['code'], nfe_result['message']
                ))
        return False

    def action_import_xml(self):
        for item in self:
            if not item.nfe_processada:
                raise UserError('Faça o download do xml antes de importar')
            invoice_eletronic = self.env['eletronic.document']
            nfe_xml = base64.decodestring(item.nfe_processada)
            nfe = objectify.fromstring(nfe_xml)

            company = item.company_id
            vals = {'nfe_mde_id': item.id}
            invoice_eletronic.import_nfe(
                company, nfe, nfe_xml, company.partner_automation,
                company.invoice_automation, company.tax_automation,
                company.supplierinfo_automation, invoice_dict=vals)
            item.is_imported = True

    def action_test_bot(self):
        self.send_message_to_user(self.env.user, 'Olá usuário, chegou uma nova nova fiscal!')