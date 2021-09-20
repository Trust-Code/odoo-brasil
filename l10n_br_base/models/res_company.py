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
    _inherit = 'res.company'

    def _compute_expiry_date(self):
        for company in self:
            company.l10n_br_cert_state = 'unknown'
            company.l10n_br_cert_information = ''
            company.l10n_br_cert_expire_date = None
            try:
                pfx = base64.decodestring(
                    company.with_context(bin_size=False).l10n_br_certificate)
                pfx = crypto.load_pkcs12(pfx, company.l10n_br_cert_password)
                cert = pfx.get_certificate()
                end = datetime.strptime(
                    cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
                subj = cert.get_subject()
                company.l10n_br_cert_expire_date = end.date()
                if datetime.now() < end:
                    company.l10n_br_cert_state = 'valid'
                else:
                    company.l10n_br_cert_state = 'expired'
                company.l10n_br_cert_information = "%s\n%s\n%s\n%s" % (
                    subj.CN, subj.L, subj.O, subj.OU)
            except crypto.Error:
                company.l10n_br_cert_state = 'invalid_password'
            except:
                _logger.warning(
                    _(u'Unknown error when validating certificate'),
                    exc_info=True)

    l10n_br_certificate = fields.Binary('Certificado A1')
    l10n_br_cert_password = fields.Char('Senha certificado', size=64)

    l10n_br_cert_state = fields.Selection(
        [('not_loaded', 'Not loaded'),
         ('expired', 'Expired'),
         ('invalid_password', 'Invalid Password'),
         ('unknown', 'Unknown'),
         ('valid', 'Valid')],
        string="Cert. State", compute='_compute_expiry_date',
        default='not_loaded')
    l10n_br_cert_information = fields.Text(
        string="Cert. Info", compute='_compute_expiry_date')
    l10n_br_cert_expire_date = fields.Date(
        string="Cert. Expiration Date", compute='_compute_expiry_date')

    @api.onchange('zip')
    def onchange_mask_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                zip = "%s-%s" % (val[0:5], val[5:8])
                self.zip = zip
