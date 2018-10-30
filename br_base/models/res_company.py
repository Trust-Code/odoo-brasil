# © 2004-2010 Tiny SPRL (<http://tiny.be>)
# © Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
# © Akretion (<http://www.akretion.com>)
# © KMEE (<http://www.kmee.com.br>)
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import re
import logging
import base64
from datetime import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except ImportError:
    _logger.error('Cannot import OpenSSL.crypto', exc_info=True)


class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = ['res.company', 'br.localization.filtering']

    @api.one
    def _get_address_data(self):
        self.city_id = self.partner_id.city_id
        self.l10n_br_district = self.partner_id.l10n_br_district
        self.l10n_br_number = self.partner_id.l10n_br_number

    @api.one
    def _get_br_data(self):
        """ Read the l10n_br specific functional fields. """
        self.l10n_br_legal_name = self.partner_id.l10n_br_legal_name
        self.l10n_br_cnpj_cpf = self.partner_id.l10n_br_cnpj_cpf
        self.l10n_br_inscr_est = self.partner_id.l10n_br_inscr_est
        self.l10n_br_inscr_mun = self.partner_id.l10n_br_inscr_mun
        self.l10n_br_suframa = self.partner_id.l10n_br_suframa

    @api.one
    def _set_br_suframa(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.l10n_br_suframa = self.l10n_br_suframa

    @api.one
    def _set_br_legal_name(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.l10n_br_legal_name = self.l10n_br_legal_name

    @api.one
    def _set_br_cnpj_cpf(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.l10n_br_cnpj_cpf = self.l10n_br_cnpj_cpf

    @api.one
    def _set_br_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.l10n_br_inscr_est = self.l10n_br_inscr_est

    @api.one
    def _set_br_inscr_mun(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.l10n_br_inscr_mun = self.l10n_br_inscr_mun

    @api.one
    def _set_br_number(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.l10n_br_number = self.l10n_br_number

    @api.one
    def _set_br_district(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.l10n_br_district = self.l10n_br_district

    @api.one
    def _set_city_id(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.city_id = self.city_id

    @api.one
    def _compute_expiry_date(self):
        try:
            pfx = base64.decodestring(
                self.with_context(bin_size=False).l10n_br_nfe_a1_file)
            pfx = crypto.load_pkcs12(pfx, self.l10n_br_nfe_a1_password)
            cert = pfx.get_certificate()
            end = datetime.strptime(
                cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
            subj = cert.get_subject()
            self.l10n_br_cert_cert_expire_date = end
            if datetime.now() < end:
                self.l10n_br_cert_state = 'valid'
            else:
                self.l10n_br_cert_state = 'expired'
            self.l10n_br_cert_information = "%s\n%s\n%s\n%s" % (
                subj.CN, subj.L, subj.O, subj.OU)
        except crypto.Error:
            self.l10n_br_cert_state = 'invalid_password'
        except:
            self.l10n_br_cert_state = 'unknown'
            _logger.warning(
                _(u'Unknown error when validating certificate'),
                exc_info=True)

    l10n_br_cnpj_cpf = fields.Char(
        compute=_get_br_data, inverse=_set_br_cnpj_cpf, size=18,
        string=u'CNPJ', oldname='cnpj_cpf')

    l10n_br_inscr_est = fields.Char(
        compute=_get_br_data, inverse=_set_br_inscr_est, size=16,
        string=u'State Inscription', oldname='inscr_est')

    l10n_br_inscr_mun = fields.Char(
        compute=_get_br_data, inverse=_set_br_inscr_mun, size=18,
        string=u'Municipal Inscription', oldname='inscr_mun')

    l10n_br_suframa = fields.Char(
        compute=_get_br_data, inverse=_set_br_suframa, size=18,
        string=u'Suframa', oldname='suframa')

    l10n_br_legal_name = fields.Char(
        compute=_get_br_data, inverse=_set_br_legal_name, size=128,
        string=u'Legal Name', oldname='legal_name')

    city_id = fields.Many2one(
        compute=_get_address_data, inverse='_set_city_id',
        comodel_name='res.city', string="City", multi='address')

    l10n_br_district = fields.Char(
        compute=_get_address_data, inverse='_set_br_district', size=32,
        string=u"District", multi='address', oldname='district')

    l10n_br_number = fields.Char(
        compute=_get_address_data, inverse='_set_br_number', size=10,
        string=u"Number", multi='address', oldname='number')

    l10n_br_nfe_a1_file = fields.Binary(u'NFe A1 File',
                                        oldname='nfe_a1_file')
    l10n_br_nfe_a1_password = fields.Char(u'NFe A1 Password', size=64,
                                          oldname='nfe_a1_password')

    l10n_br_cert_state = fields.Selection(
        [('not_loaded', u'Not loaded'),
         ('expired', u'Expired'),
         ('invalid_password', u'Invalid Password'),
         ('unknown', u'Unknown'),
         ('valid', u'Valid')],
        string=u"Cert. State", compute=_compute_expiry_date,
        default='not_loaded', oldname='cert_state')
    l10n_br_cert_information = fields.Text(
        string=u"Cert. Info", compute=_compute_expiry_date,
        oldname='cert_information')
    l10n_br_cert_expire_date = fields.Date(
        string=u"Cert. Expiration Date", compute=_compute_expiry_date,
        oldname='cert_expire_date')

    @api.onchange('l10n_br_cnpj_cpf')
    def onchange_mask_cnpj_cpf(self):
        if self.l10n_br_cnpj_cpf:
            val = re.sub('[^0-9]', '', self.l10n_br_cnpj_cpf)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.l10n_br_cnpj_cpf = cnpj_cpf

    @api.onchange('city_id')
    def onchange_city_id(self):
        """ Ao alterar o campo city_id copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        """
        if self.city_id:
            self.city = self.city_id.name

    @api.onchange('zip')
    def onchange_mask_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                zip = "%s-%s" % (val[0:5], val[5:8])
                self.zip = zip
