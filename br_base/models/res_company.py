# -*- coding: utf-8 -*-
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
    _logger.debug('Cannot import OpenSSL.crypto', exc_info=True)


class ResCompany(models.Model):

    _inherit = 'res.company'

    @api.one
    def _get_address_data(self):
        self.city_id = self.partner_id.city_id
        self.district = self.partner_id.district
        self.number = self.partner_id.number

    @api.one
    def _get_br_data(self):
        """ Read the l10n_br specific functional fields. """
        self.legal_name = self.partner_id.legal_name
        self.cnpj_cpf = self.partner_id.cnpj_cpf
        self.inscr_est = self.partner_id.inscr_est
        self.inscr_mun = self.partner_id.inscr_mun
        self.suframa = self.partner_id.suframa

    @api.one
    def _set_br_suframa(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.suframa = self.suframa

    @api.one
    def _set_br_legal_name(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.legal_name = self.legal_name

    @api.one
    def _set_br_cnpj_cpf(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.cnpj_cpf = self.cnpj_cpf

    @api.one
    def _set_br_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.inscr_est = self.inscr_est

    @api.one
    def _set_br_inscr_mun(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.inscr_mun = self.inscr_mun

    @api.one
    def _set_br_number(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.number = self.number

    @api.one
    def _set_br_district(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.district = self.district

    @api.one
    def _set_city_id(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.city_id = self.city_id

    @api.one
    def _compute_expiry_date(self):
        try:
            pfx = base64.decodestring(
                self.with_context(bin_size=False).nfe_a1_file)
            pfx = crypto.load_pkcs12(pfx, self.nfe_a1_password)
            cert = pfx.get_certificate()
            end = datetime.strptime(
                cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
            subj = cert.get_subject()
            self.cert_expire_date = end
            if datetime.now() < end:
                self.cert_state = 'valid'
            else:
                self.cert_state = 'expired'
            self.cert_information = "%s\n%s\n%s\n%s" % (
                subj.CN, subj.L, subj.O, subj.OU)
        except crypto.Error:
            self.cert_state = 'invalid_password'
        except:
            self.cert_state = 'unknown'
            _logger.warning(
                _(u'Unknown error when validating certificate'),
                exc_info=True)

    cnpj_cpf = fields.Char(
        compute=_get_br_data, inverse=_set_br_cnpj_cpf, size=18,
        string=u'CNPJ')

    inscr_est = fields.Char(
        compute=_get_br_data, inverse=_set_br_inscr_est, size=16,
        string=u'State Inscription')

    inscr_mun = fields.Char(
        compute=_get_br_data, inverse=_set_br_inscr_mun, size=18,
        string=u'Municipal Inscription')

    suframa = fields.Char(
        compute=_get_br_data, inverse=_set_br_suframa, size=18,
        string=u'Suframa')

    legal_name = fields.Char(
        compute=_get_br_data, inverse=_set_br_legal_name, size=128,
        string=u'Legal Name')

    city_id = fields.Many2one(
        compute=_get_address_data, inverse='_set_city_id',
        comodel_name='res.state.city', string="City", multi='address')

    district = fields.Char(
        compute=_get_address_data, inverse='_set_br_district', size=32,
        string=u"District", multi='address')

    number = fields.Char(
        compute=_get_address_data, inverse='_set_br_number', size=10,
        string=u"Number", multi='address')

    nfe_a1_file = fields.Binary(u'NFe A1 File')
    nfe_a1_password = fields.Char(u'NFe A1 Password', size=64)

    cert_state = fields.Selection(
        [('not_loaded', u'Not loaded'),
         ('expired', u'Expired'),
         ('invalid_password', u'Invalid Password'),
         ('unknown', u'Unknown'),
         ('valid', u'Valid')],
        string=u"Cert. State", compute=_compute_expiry_date,
        default='not_loaded')
    cert_information = fields.Text(
        string=u"Cert. Info", compute=_compute_expiry_date)
    cert_expire_date = fields.Date(
        string=u"Cert. Expiration Date", compute=_compute_expiry_date)

    @api.onchange('cnpj_cpf')
    def onchange_mask_cnpj_cpf(self):
        if self.cnpj_cpf:
            val = re.sub('[^0-9]', '', self.cnpj_cpf)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.cnpj_cpf = cnpj_cpf

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
