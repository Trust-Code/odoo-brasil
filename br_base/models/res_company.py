# -*- coding: utf-8 -*-
# © 2004-2010 Tiny SPRL (<http://tiny.be>)
# © Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
# © Akretion (<http://www.akretion.com>)
# © KMEE (<http://www.kmee.com.br>)
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import re
from odoo import models, fields, api


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

    cnpj_cpf = fields.Char(
        compute=_get_br_data, inverse=_set_br_cnpj_cpf, size=18,
        string='CNPJ')

    inscr_est = fields.Char(
        compute=_get_br_data, inverse=_set_br_inscr_est, size=16,
        string='Inscr. Estadual')

    inscr_mun = fields.Char(
        compute=_get_br_data, inverse=_set_br_inscr_mun, size=18,
        string='Inscr. Municipal')

    suframa = fields.Char(
        compute=_get_br_data, inverse=_set_br_suframa, size=18,
        string='Suframa')

    legal_name = fields.Char(
        compute=_get_br_data, inverse=_set_br_legal_name, size=128,
        string=u'Razão Social')

    city_id = fields.Many2one(
        compute=_get_address_data, inverse='_set_city_id',
        comodel_name='res.state.city', string="City", multi='address')

    district = fields.Char(
        compute=_get_address_data, inverse='_set_br_district', size=32,
        string="Bairro", multi='address')

    number = fields.Char(
        compute=_get_address_data, inverse='_set_br_number', size=10,
        string=u"Número", multi='address')

    nfe_a1_file = fields.Binary('Arquivo NFe A1')
    nfe_a1_password = fields.Char('Senha NFe A1', size=64)

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
