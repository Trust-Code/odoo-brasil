import re
import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)

try:
    from pytrustnfe.nfe import consulta_cadastro
    from pytrustnfe.certificado import Certificado
except ImportError:
    _logger.error('Cannot import pytrustnfe', exc_info=True)


class ResPartner(models.Model):
    _inherit = [
        'res.partner',
        'zip.search.mixin',
    ]
    _name = 'res.partner'

    l10n_br_legal_name = fields.Char('Legal Name', size=60)
    l10n_br_cnpj_cpf = fields.Char('CNPJ/CPF', size=20)
    l10n_br_district = fields.Char('District', size=60)
    l10n_br_number = fields.Char('Number', size=10)
    l10n_br_inscr_est = fields.Char('Inscr. Estadual', size=20)
    l10n_br_inscr_mun = fields.Char('Inscr. Municipal', size=20)
    l10n_br_suframa = fields.Char('Suframa', size=20)

    _sql_constraints = [
        ('res_partner_l10n_br_cnpj_cpf_uniq', 'unique (l10n_br_cnpj_cpf)',
         'Este CPF/CNPJ já está em uso por outro parceiro!')
    ]

    def _formatting_address_fields(self):
        fields = super(ResPartner, self)._formatting_address_fields()
        return fields + ['l10n_br_district', 'l10n_br_number']

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name
            self.state_id = self.city_id.state_id

    @api.onchange('zip')
    def _onchange_zip(self):
        cep = re.sub('[^0-9]', '', self.zip or '')
        if cep and len(cep) == 8:
            vals = self.search_address_by_zip(cep)
            self.update(vals)
        elif cep:
            return {
                'warning': {
                    'title': 'Tip',
                    'message': 'Please use a 8 number value to search ;)'
                }
            }

    @api.onchange('l10n_br_cnpj_cpf')
    def _onchange_l10n_br_cnpj_cpf(self):
        country_code = self.country_id.code or ''
        if self.l10n_br_cnpj_cpf and country_code.upper() == 'BR':
            val = re.sub('[^0-9]', '', self.l10n_br_cnpj_cpf)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.l10n_br_cnpj_cpf = cnpj_cpf
            elif not self.is_company and len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                    % (val[0:3], val[3:6], val[6:9], val[9:11])
                self.l10n_br_cnpj_cpf = cnpj_cpf

    @api.model
    def install_default_country(self):
        IrDefault = self.env['ir.default']
        default_value = IrDefault.get('res.partner', 'country_id')
        if default_value is None:
            IrDefault.set('res.partner', 'country_id', self.env.ref('base.br').id)
        return True

    def action_check_sefaz(self):
        if self.l10n_br_cnpj_cpf and self.state_id:
            if self.state_id.code == 'AL':
                raise UserError(_(u'Alagoas doesn\'t have this service'))
            if self.state_id.code == 'RJ':
                raise UserError(_(
                    u'Rio de Janeiro doesn\'t have this service'))
            company = self.env.company
            if not company.l10n_br_certificate and not company.l10n_br_cert_password:
                raise UserError(_(
                    u'Configure the company\'s certificate and password'))
            cert = company.with_context({'bin_size': False}).l10n_br_certificate
            cert_pfx = base64.decodestring(cert)
            certificado = Certificado(cert_pfx, company.l10n_br_cert_password)
            cnpj = re.sub('[^0-9]', '', self.l10n_br_cnpj_cpf)
            obj = {'cnpj': cnpj, 'estado': self.state_id.code}
            resposta = consulta_cadastro(certificado, obj=obj, ambiente=1,
                                         estado=self.state_id.l10n_br_ibge_code)

            info = resposta['object'].getchildren()[0]
            info = info.infCons
            if info.cStat == 111 or info.cStat == 112:
                if not self.l10n_br_inscr_est:
                    self.l10n_br_inscr_est = info.infCad.IE.text
                if not self.l10n_br_cnpj_cpf:
                    self.l10n_br_cnpj_cpf = info.infCad.CNPJ.text

                def get_value(obj, prop):
                    if prop not in dir(obj):
                        return None
                    return getattr(obj, prop)
                self.l10n_br_legal_name = get_value(info.infCad, 'xNome')
                if "ender" not in dir(info.infCad):
                    return
                cep = get_value(info.infCad.ender, 'CEP') or ''
                self.zip = str(cep).zfill(8) if cep else ''
                self.street = get_value(info.infCad.ender, 'xLgr')
                self.l10n_br_number = get_value(info.infCad.ender, 'nro')
                self.street2 = get_value(info.infCad.ender, 'xCpl')
                self.l10n_br_district = get_value(info.infCad.ender, 'xBairro')
                cMun = get_value(info.infCad.ender, 'cMun')
                xMun = get_value(info.infCad.ender, 'xMun')
                city = None
                if cMun:
                    city = self.env['res.city'].search(
                        [('l10n_br_ibge_code', '=', str(cMun)[2:]),
                         ('state_id', '=', self.state_id.id)])
                if not city and xMun:
                    city = self.env['res.city'].search(
                        [('name', 'ilike', xMun),
                         ('state_id', '=', self.state_id.id)])
                if city:
                    self.city_id = city.id
            else:
                msg = "%s - %s" % (info.cStat, info.xMotivo)
                raise UserError(msg)
        else:
            raise UserError(_('Fill the State and CNPJ fields to search'))

