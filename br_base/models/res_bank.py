# -*- coding: utf-8 -*-
# © 2009 Gabriel C. Stabel
# © 2009 Renato Lima (Akretion)
# © 2012 Raphaël Valyi (Akretion)
# © 2015  Michell Stuttgart (KMEE)
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResBank(models.Model):
    _inherit = 'res.bank'

    number = fields.Char(u'Número', size=10)
    street2 = fields.Char('Complemento', size=128)
    district = fields.Char('Bairro', size=32)
    city_id = fields.Many2one(comodel_name='res.state.city',
                              string=u'Município',
                              domain="[('state_id','=',state_id)]")

    country_id = fields.Many2one(comodel_name='res.country',
                                 related='country',
                                 string=u'País')
    state_id = fields.Many2one(comodel_name='res.country.state',
                               related='state',
                               string='Estado')

    @api.onchange('city_id')
    def onchange_city_id(self):
        """ Ao alterar o campo city_id copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        """
        if self.city_id:
            self.city = self.city_id.name


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    acc_number = fields.Char('Account Number', size=64, required=False)
    acc_number_dig = fields.Char(u'Digito Conta', size=8)
    bra_number = fields.Char(u'Agência', size=8)
    bra_number_dig = fields.Char(u'Dígito Agência', size=8)
