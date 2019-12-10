
from odoo import api, fields, models


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
        if self.zip and len(self.zip) == 8:
            vals = self.search_address_by_zip(self.zip)
            self.update(vals)
        elif self.zip:
            return {
                'warning': {
                    'title': 'Tip',
                    'message': 'Please use a 8 number value to search ;)'
                }
            }

    @api.model
    def install_default_country(self):
        IrDefault = self.env['ir.default']
        default_value = IrDefault.get('res.partner', 'country_id')
        if default_value is None:
            IrDefault.set('res.partner', 'country_id', self.env.ref('base.br').id)
        return True
