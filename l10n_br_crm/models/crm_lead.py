# -*- coding: utf-8 -*-
# © 2012  Renato Lima - Akretion
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import models, fields, api, _
from odoo.addons.l10n_br_base.tools import fiscal
from odoo.exceptions import UserError


class CrmLead(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    legal_name = fields.Char(u'Razão Social', size=60,
                             help="Nome utilizado em documentos fiscais")
    cnpj = fields.Char('CNPJ', size=18,  oldname='cnpj_cpf')
    inscr_est = fields.Char('Inscr. Estadual', size=16)
    inscr_mun = fields.Char('Inscr. Municipal', size=18)
    suframa = fields.Char('Suframa', size=18)
    city_id = fields.Many2one('res.state.city', 'Municipio',
                              domain="[('state_id','=',state_id)]")
    district = fields.Char('Bairro', size=32)
    number = fields.Char('Número', size=10)
    name_surname = fields.Char(u'Nome e Sobrenome', size=128,
                               help="Nome utilizado em documentos fiscais")
    cpf = fields.Char('CPF', size=18)
    rg = fields.Char('RG', size=16)

    @api.one
    @api.constrains('cnpj')
    def _check_cnpj(self):
        if self.cnpj:
            if not fiscal.validate_cnpj(self.cnpj):
                raise UserError(_(u'CNPJ inválido!'))
        return True

    @api.one
    @api.constrains('cpf')
    def _check_cpf(self):
        if self.cpf:
            if not fiscal.validate_cpf(self.cpf):
                raise UserError(_(u'CPF inválido!'))
        return True

    def _validate_ie_param(self, uf, inscr_est):
        try:
            mod = __import__(
                'odoo.addons.l10n_br_base.tools.fiscal',
                globals(), locals(), 'fiscal')

            validate = getattr(mod, 'validate_ie_%s' % uf)
            if not validate(inscr_est):
                return False
        except AttributeError:
            if not fiscal.validate_ie_param(uf, inscr_est):
                return False
        return True

    @api.one
    @api.constrains('inscr_est')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False."""
        if (not self.inscr_est or self.inscr_est == 'ISENTO'):
            return True
        uf = (self.state_id and
              self.state_id.code.lower() or '')
        res = self._validate_ie_param(uf, self.inscr_est)
        if not res:
            raise Warning(_(u'Inscrição Estadual inválida!'))
        return True

    @api.onchange('cnpj')
    def onchange_mask_cnpj(self):
        if self.cnpj:
            val = re.sub('[^0-9]', '', self.cnpj)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.cnpj = cnpj_cpf
            else:
                raise Warning(_(u'Verifique o CNPJ'))

    @api.onchange('cpf')
    def onchange_mask_cpf(self):
        if self.cnpj:
            val = re.sub('[^0-9]', '', self.cpf)
            if len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                    % (val[0:3], val[3:6], val[6:9], val[9:11])
                self.cpf = cnpj_cpf
            else:
                raise Warning(_(u'Verifique o CPF'))

    @api.onchange('city_id')
    def onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # TODO Melhorar esse metodo e setar os campos corretamente
        if self.partner_id:
            self.legal_name = self.partner_id.legal_name
            self.cnpj_cpf = self.partner_id.cnpj_cpf
            self.inscr_est = self.partner_id.inscr_est
            self.suframa = self.partner_id.suframa
            self.number = self.partner_id.number
            self.district = self.partner_id.district
            self.city_id = self.partner_id.city_id.id

    @api.model
    def _lead_create_contact(self, lead, name, is_company, parent_id=False):
        id = super(CrmLead, self)._lead_create_contact(
            lead, name, is_company, parent_id)
        value = {
            'number': lead.number,
            'district': lead.district,
            'l10n_br_city_id': lead.l10n_br_city_id.id
        }
        if is_company:
            value.update({
                'legal_name': lead.legal_name,
                'cnpj_cpf': lead.cnpj,
                'inscr_est': lead.inscr_est,
                'inscr_mun': lead.inscr_mun,
                'suframa': lead.suframa,
                })
        else:
            value.update({
                'legal_name': lead.name_surname,
                'cnpj_cpf': lead.cpf,
                'inscr_est': lead.rg,
                })
        if id:
            partner = self.env['res.partner'].browse(id)
            partner[0].write(value)
        return id
