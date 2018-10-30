# © 2009 Gabriel C. Stabel
# © 2009 Renato Lima (Akretion)
# © 2012 Raphaël Valyi (Akretion)
# © 2015  Michell Stuttgart (KMEE)
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.addons.base.res.res_bank import sanitize_account_number


class ResBank(models.Model):
    _name = 'res.bank'
    _inherit = ['res.bank', 'br.localization.filtering']

    l10n_br_number = fields.Char(u'Number', size=10, oldname='number')
    street2 = fields.Char('Complement', size=128)
    l10n_br_district = fields.Char('District', size=32, oldname='district')
    city_id = fields.Many2one(comodel_name='res.city',
                              string=u'City',
                              domain="[('state_id','=',state_id)]")

    country_id = fields.Many2one(comodel_name='res.country',
                                 related='country',
                                 string=u'Country')
    state_id = fields.Many2one(comodel_name='res.country.state',
                               related='state',
                               string='State')

    l10n_br_acc_number_format = fields.Text(help="""You can enter here the \
    format as the bank accounts are referenced in ofx files for the import of \
    bank statements.\nYou can use the python patern string with the entire \
    bank account field.\nValid Fields:\n
          %(l10n_br_number): Bank Branch Number\n
          %(l10n_br_number_dig): Bank Branch Number's Digit\n
          %(acc_number): Bank Account Number\n
          %(acc_number_dig): Bank Account Number's Digit\n
    For example, use '%(acc_number)s' to display the field 'Bank Account \
    Number' plus '%(acc_number_dig)s' to display the field 'Bank Account \
    Number s Digit'.""", default='%(acc_number)s', oldname='acc_number_format')

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
    _name = 'res.partner.bank'
    _inherit = ['res.partner.bank', 'br.localization.filtering']

    acc_number = fields.Char('Account Number', size=64, required=False)
    acc_number_dig = fields.Char('Account Number Digit', size=8)
    l10n_br_number = fields.Char('Agency', size=8, oldname='bra_number')
    l10n_br_number_dig = fields.Char('Account Agency Digit', size=8,
                                     oldname='bra_number_dig')

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "cc: %s-%s - %s - %s" % (
                rec.acc_number, rec.acc_number_dig or '',
                rec.partner_id.name or '', rec.bank_id.name or '')))
        return result

    @api.depends('bank_id', 'acc_number', 'acc_number_dig',
                 'l10n_br_number', 'l10n_br_number_dig')
    def _compute_sanitized_acc_number(self):
        for bank_account in self:
            if bank_account.bank_id:
                l10n_br_acc_number_format = \
                    (bank_account.bank_id.l10n_br_acc_number_format
                     or '%(acc_number)s')
                args = {
                    'l10n_br_number': bank_account.l10n_br_number or '',
                    'l10n_br_number_dig': (bank_account.l10n_br_number_dig
                                           or ''),
                    'acc_number': bank_account.acc_number or '',
                    'acc_number_dig': bank_account.acc_number_dig or ''
                }
                self.sanitized_acc_number = sanitize_account_number(
                    l10n_br_acc_number_format % args)
            else:
                self.sanitized_acc_number = sanitize_account_number(
                    bank_account.acc_number)
