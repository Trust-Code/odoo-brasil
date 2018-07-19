# -*- coding: utf-8 -*-

import base64, re, logging, zlib, pytz
from lxml import etree, objectify
from datetime import datetime
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import Warning, UserError

_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import xml_consulta_distribuicao_nfe
    from pytrustnfe.nfe import consulta_distribuicao_nfe
    from pytrustnfe.nfe import xml_download_nfe
    from pytrustnfe.nfe import download_nfe
    from pytrustnfe.certificado import Certificado

except ImportError:
    _logger.info('Cannot import pytrustnfe', exc_info=True)

class SpedDFeQueryWizard(models.TransientModel):

    _name = 'sped.dfe.query.wizard'

    company_id = fields.Many2one('res.company', u'Empresa', readonly=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))
    ambiente = fields.Selection([('homologacao', 'Homologação'), ('producao', 'Produção')], readonly=True,
                                string='Ambiente de Consulta', related='company_id.tipo_ambiente')
    cnpj_cpf = fields.Char(string='CNPJ/CPF do Autor', related='company_id.cnpj_cpf')
    chave_nfe = fields.Char(string='Chave de Acesso Específica')
    type_query = fields.Selection([('all', 'Forçar Consultas'), ('ultimo_nsu', 'Buscar apartir do último NSU Baixado'),
                                   ('chave_nfe', 'Buscar uma NF-e específica')], 'Tipo de Busca', default='ultimo_nsu')


    @api.multi
    def automated_search_dfe(self):
        nsus = self.env['sped.dfe.query'].search([])
        count_nsus = len(nsus)
        company_id = self.env['res.company']._company_default_get('account.account')
        if count_nsus == 0:
            active_ids = self.env['sped.dfe.query.wizard'].create({
                'company_id': company_id.id,
                'cnpj_cpf': company_id.cnpj_cpf,
                'ambiente': company_id.tipo_ambiente,
                'type_query': 'all'
            })
        elif count_nsus > 0:
            active_ids = self.env['sped.dfe.query.wizard'].create({
                'company_id': company_id.id,
                'cnpj_cpf': company_id.cnpj_cpf,
                'ambiente': company_id.tipo_ambiente,
                'type_query': 'ultimo_nsu'
            })
        for search in active_ids:
            search.dfe_query()


    @api.onchange('type_query')
    def validate_type_query(self):
        if self.type_query == 'ultimo_nsu':
            self.chave_nfe = None

        elif self.type_query == 'all':
            self.chave_nfe = None

        elif self.type_query == 'chave_nfe':
            self.ultimo_nsu = None

    @api.multi
    def validate_query(self):
        if self.type_query == 'chave_nfe' and len(self.chave_nfe) != 44:
            raise UserError(u'A Chave de NF-e informada é inválida.')

    @api.multi
    def _prepare_dfe_query_values(self):
        vals = {
            'ambiente': 1 if self.ambiente == '1' else 2,
            'estado': self.company_id.partner_id.state_id.ibge_code,
            'cnpj_cpf': re.sub('[^0-9]', '', self.company_id.cnpj_cpf)
        }

        if self.type_query == 'chave_nfe':
            vals['chave_nfe'] = self.chave_nfe

        elif self.type_query == 'ultimo_nsu':
            lista_nsu = self.env['sped.dfe.query.nsu'].search([]).mapped('nsu')
            ultimo_nsu = max(lista_nsu)
            vals['ultimo_nsu'] = ((15 - len(str(ultimo_nsu))) * '0') + str(ultimo_nsu)\
                if len(str(ultimo_nsu)) < 15 else ''
        elif self.type_query == 'all':
            vals['ultimo_nsu'] = '000000000000001'

        return vals

    @api.multi
    def _prepare_xml_dfe_query(self):
        lote = self._prepare_dfe_query_values()

        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        xml_enviar = xml_consulta_distribuicao_nfe(certificado, **lote)
        xml_to_send = base64.encodestring(xml_enviar.encode('utf-8'))

        return xml_to_send

    @api.multi
    def process_nsu(self, nsu):
        import pudb;pu.db
        data = nsu.text
        decoded_data = zlib.decompress(base64.b64decode(data), 16 + zlib.MAX_WBITS)
        xml = objectify.fromstring(decoded_data)
        decoded_data = base64.b64encode(decoded_data)
        schema = nsu.attrib['schema']

        vals = {}
        # Busca os Valores no XML de Resumo da NF-e
        # Esquema de Resumo de uma NF-e gerada por um fornecedor
        if schema == 'resNFe_v1.01.xsd':
            vals['cnpj'] = xml.CNPJ.text
            vals['xnome'] = xml.xNome
            vals['ie'] = xml.IE.text
            vals['nsu_type'] = 'res_nfe'
            vals['chave_nfe'] = xml.chNFe.text
            vals['nfe_state'] = xml.cSitNFe.text
            vals['valor_nfe'] = xml.vNF
            vals['tpnf'] = xml.tpNF
            data_evento = xml.dhEmi.text[0:10]
            data_evento = datetime.strptime(data_evento, '%Y-%m-%d').date()
            vals['data_evento'] = data_evento
        # Busca os Valores no XML de uma NF-e
        # XML de NF-e de um Fornecedor
        elif schema == 'procNFe_v3.10.xsd' or schema == 'procNFe_v4.00.xsd':
            vals['cnpj'] = xml.NFe.infNFe.emit.CNPJ.text
            vals['xnome'] = xml.NFe.infNFe.emit.xNome
            vals['ie'] = xml.NFe.infNFe.emit.IE.text
            vals['tpnf'] = xml.NFe.infNFe.ide.tpNF
            vals['valor_nfe'] = xml.NFe.infNFe.total.ICMSTot.vNF
            vals['chave_nfe'] = xml.protNFe.infProt.chNFe
            vals['nsu_type'] = 'nfe'
            data_evento = xml.protNFe.infProt.dhRecbto.text[0:10]
            data_evento = datetime.strptime(data_evento, '%Y-%m-%d').date()
            vals['data_evento'] = data_evento
        # Busca os Valores no XML de Resumo de um Evento
        # Resumos de Eventos gerados gerados por mim sobre um documento gerado por um fornecedor
        elif schema == 'resEvento_v1.01.xsd':
            vals['cnpj'] = xml.CNPJ.text
            vals['chave_nfe'] = xml.chNFe
            vals['nsu_type'] = 'res_evento'
            vals['cod_evento'] = xml.tpEvento
            vals['nome_evento'] = xml.xEvento
            data_evento = xml.dhEvento.text[0:10]
            data_evento = datetime.strptime(data_evento, '%Y-%m-%d').date()
            vals['data_evento'] = data_evento
        # Busca os Valores no XML de proceso de Evento
        # Quando um cliente se manifesta sobre um doc. emitido pela empresa
        elif schema == 'procEventoNFe_v1.00.xsd':
            vals['cnpj'] = xml.evento.infEvento.CNPJ.text
            vals['nsu_type'] = 'proc_evento'
            vals['chave_nfe'] = xml.evento.infEvento.chNFe
            vals['cod_evento'] = xml.evento.infEvento.tpEvento
            vals['nome_evento'] = xml.evento.infEvento.detEvento.descEvento
            data_evento = xml.evento.infEvento.dhEvento.text[0:10]
            data_evento = datetime.strptime(data_evento, '%Y-%m-%d').date()
            vals['data_evento'] = data_evento

        vals['company_id'] = self.company_id.id
        vals['nsu'] = nsu.attrib['NSU']
        vals['xml'] = decoded_data
        if schema != 'procNFe_v3.10.xsd' or 'procNFe_v4.00.xsd':
            vals['xml_name'] = 'NSU-%s.xml' % nsu.attrib['NSU']
        else:
            vals['xml_name'] = 'NFe-%s.xml' % xml.NFe.infNFe.ide.nNF

        return vals

    @api.multi
    def dfe_query(self):
        self.validate_query()
        query = self._prepare_xml_dfe_query()
        xml_to_send = base64.decodestring(query).decode('utf-8')
        cert = self.company_id.with_context({'bin_size': False}).nfe_a1_file
        cert_pfx = base64.decodestring(cert)
        certificado = Certificado(cert_pfx, self.company_id.nfe_a1_password)

        tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc
        dt_evento = datetime.utcnow()
        dt_evento = pytz.utc.localize(dt_evento).astimezone(tz)
        data = dt_evento.strftime('%Y-%m-%dT%H:%M')

        resposta = consulta_distribuicao_nfe(certificado, estado=self.company_id.partner_id.state_id.ibge_code,
                                        ambiente=1 if self.ambiente == '1' else 2, modelo='consulta', xml=xml_to_send)

        retorno = resposta['object'].Body.nfeDistDFeInteresseResponse.nfeDistDFeInteresseResult.getchildren()[0]
        if retorno.cStat != 138:
            return {
                'name': 'Messagem',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sped.dfe.query.cstat',
                'target': 'new',
                'context': {'default_message': str(retorno.cStat) + ' - ' + str(retorno.xMotivo)}
            }
        if retorno.cStat == 138 and self.chave_nfe == False:
            resultado = self.env['sped.dfe.query']
            xml_received = base64.b64encode(bytes(resposta['received_xml'], 'utf-8'))

            vals = {
                'ultNSU': retorno.ultNSU,
                'maxNSU':retorno.maxNSU,
                'dhResp': retorno.dhResp,
                'xml_received': xml_received,
            }

            res = resultado.create(vals)
            nsus = []

            for doc in retorno.loteDistDFeInt.docZip:
                nsu = self.env['sped.dfe.query.nsu']
                vals_nsu = self.process_nsu(nsu=doc)
                vals_nsu['query_ids'] = [(6, _, [res.id])]
                if len(nsu.search([('nsu', '=', vals_nsu['nsu'])])) == 0:
                    new_nsu = nsu.create(vals_nsu)
                    nsus.append(new_nsu.nsu)
            if len(nsus) == 0:
                raise Warning(u'Não há nenhum novo evento para Baixar')
            elif len(nsus) > 0:
                lowest_nsu = min(nsus)
                greater_nsu = max(nsus)
                res.lowest_nsu = lowest_nsu
                res.greater_nsu = greater_nsu
                res.xml_name = '%s.xml' % (str(lowest_nsu) + ' - ' + str(greater_nsu))
                res.name = 'CONSULTA - ' + data + ' NSU '\
                + str(res.lowest_nsu) + ' ATÉ ' + str(res.greater_nsu)

        elif retorno.cStat == 138 and self.chave_nfe != False:
            for doc in retorno.loteDistDFeInt.docZip:
                query_nsu = self.env['sped.dfe.query.nsu'].search([('chave_nfe', '=', self.chave_nfe)])
                data = doc.text
                decoded_data = zlib.decompress(base64.b64decode(data), 16 + zlib.MAX_WBITS)
                decoded_data = base64.b64encode(decoded_data)
                query_nsu.nfe_xml = decoded_data

class SpedDFeQuerycStat(models.TransientModel):
    _name = 'sped.dfe.query.cstat'

    message = fields.Char('Message')