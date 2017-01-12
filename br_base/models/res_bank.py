# -*- coding: utf-8 -*-
# © 2009 Gabriel C. Stabel
# © 2009 Renato Lima (Akretion)
# © 2012 Raphaël Valyi (Akretion)
# © 2015  Michell Stuttgart (KMEE)
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# © 2017 Carlos Alberto Cipriano Korovsky <carlos.korovsky@uktech.com.br>, UKTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


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
    
    acc_number_format = fields.Text(help="""You can enter here the format as\
the bank accounts are referenced in ofx files for the import of bank\
statements.\nYou can use the python patern string with the entire bank account\n
field.\nValid Fields:\n
      %(brl_bra_number): Bank Branch Number\n
      %(brl_bra_number_digit): Bank Branch Number's Digit\n
      %(brl_acc_number): Bank Account Number\n
      %(brl_acc_number_digit): Bank Account Number's Digit\n
For example, use '%(brl_acc_number)s' to display the field 'Bank Account \
Number' plus '%(brl_bra_number_digit)s' to display the field 'Bank Account \
Number s Digit'.""",
            default='%(brl_acc_number)s')

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

    acc_number = fields.Char(string='Account Number', size=256, required=False,
        store=True, readonly=False, compute='_compute_acc_number')

    brl_bra_number = fields.Char(oldname='bra_number', 
        string='Bank Branch Number', size=32, required=False)
    brl_bra_number_digit = fields.Char(oldname='bra_number_dig',
        string='Bank Branch Number\'s Digit', size=32, required=False)
    brl_acc_number = fields.Char(string='Account Number', 
        size=32, required=True)
    brl_acc_number_digit = fields.Char(oldname='acc_number_dig',
        string= 'Account Number\'s Digit', size=32, required=False)
    
    @api.depends('bank_id', 'brl_acc_number')
    def _compute_acc_number(self):
        if (self.bank_id):
            acc_number_format = self.bank_id.acc_number_format or ''
            args = {
                'brl_bra_number': self.brl_bra_number or '',
                'brl_bra_number_digit': self.brl_bra_number_digit or '',
                'brl_acc_number': self.brl_acc_number or '',
                'brl_acc_number_digit': self.brl_acc_number_digit or ''
            }
            self.acc_number = acc_number_format % args
    