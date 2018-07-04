# -*- coding: utf-8 -*-
# © 2012  Renato Lima - Akretion
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import models, fields, api, _
from odoo.addons.br_base.tools import fiscal
from odoo.exceptions import UserError


class CrmLead(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    legal_name = fields.Char(u'Razão Social', size=60,
                             help="Nome utilizado em documentos fiscais")
    cnpj = fields.Char('CNPJ', size=18)
    inscr_est = fields.Char(u'Inscrição Estadual', size=16)
    inscr_mun = fields.Char(u'Inscrição Municipal', size=18)
    suframa = fields.Char('Suframa', size=18)
    city_id = fields.Many2one('res.state.city', u'Município',
                              domain="[('state_id','=',state_id)]")
    district = fields.Char('Bairro', size=32)
    number = fields.Char(u'Número', size=10)
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
                'odoo.addons.br_base.tools.fiscal',
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
        if not self.inscr_est or self.inscr_est == 'ISENTO':
            return True
        uf = self.state_id and self.state_id.code.lower() or ''
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
        if self.cpf:
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

    def _onchange_partner_id_values(self, partner_id):
        res = super(CrmLead, self)._onchange_partner_id_values(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            val = re.sub('[^0-9]', '', partner.cnpj_cpf or '')
            if len(val) == 11:
                cnpj_cpf = 'cpf'
            else:
                cnpj_cpf = 'cnpj'
            res.update({
                'legal_name': partner.legal_name,
                cnpj_cpf: partner.cnpj_cpf,
                'inscr_est': partner.inscr_est,
                'suframa': partner.suframa,
                'number': partner.number,
                'district': partner.district,
                'city_id': partner.city_id.id,
            })
        return res

    @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        partner = super(CrmLead, self)._create_lead_partner_data(
            name, is_company, parent_id)
        partner.update({
            'number': self.number,
            'district': self.district,
            'city_id': self.city_id.id
        })
        if is_company:
            partner.update({
                'legal_name': self.legal_name,
                'cnpj_cpf': self.cnpj,
                'inscr_est': self.inscr_est,
                'inscr_mun': self.inscr_mun,
                'suframa': self.suframa,
                })
        else:
            partner.update({
                'legal_name': self.name_surname,
                'cnpj_cpf': self.cpf,
                'inscr_est': self.rg,
                })
        return partner

    @api.model
    def create(self, vals):
        vals.update(self._onchange_partner_id_values(
            vals['partner_id'] if vals.get('partner_id') else False))
        return super(CrmLead, self).create(vals)
