# © 2009  Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    bc_code = fields.Char(u'BC Code', size=5)
    ibge_code = fields.Char(u'IBGE Code', size=5)
    siscomex_code = fields.Char(u'Siscomex Code', size=4)

    def _check_address_format(self):
        for record in self:
            if record.address_format:
                address_fields = self.env['res.partner']._formatting_address_fields() + ['city_name', 'state_code', 'state_name', 'country_code', 'country_name', 'company_name']
                try:
                    record.address_format % {i: 1 for i in address_fields}
                except (ValueError, KeyError):
                    raise UserError(_('The layout contains an invalid format key'))


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    ibge_code = fields.Char(u'IBGE Code', size=2)
