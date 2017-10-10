# -*- coding: utf-8 -*-
# © 2017 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    region_ids = fields.Many2many('res.region', string="Regiões")

    def _get_partner_pricelist(self, partner_id, company_id=None):
        """ Retrieve the applicable pricelist for a given partner in a
            given company.

            :param company_id: if passed, used for looking up properties,
             instead of current user's company
        """
        Partner = self.env['res.partner']
        Property = self.env['ir.property'].with_context(
            force_company=company_id or self.env.user.company_id.id)

        p = Partner.browse(partner_id)
        pl = Property.get('property_product_pricelist',
                          Partner._name, '%s,%s' % (Partner._name, p.id))
        if pl:
            pl = pl[0].id

        if not pl:
            if p.country_id.code:
                pls = self.env['product.pricelist'].search(
                    [('country_group_ids.country_ids.code', '=',
                      p.country_id.code)], limit=1)
                pl = pls and pls[0].id

        if not pl:
            if p.state_id:
                pls = self.env['product.pricelist'].search(
                    [('region_ids.state_ids.id', '=', p.state_id.id)], limit=1)
                pl = pls and pls[0].id

        if not pl:
            if p.city_id:
                pls = self.env['product.pricelist'].search(
                    [('region_ids.city_ids.id', '=', p.city_id.id)], limit=1)
                pl = pls and pls[0].id

        if not pl:
            # search pl where no country
            pls = self.env['product.pricelist'].search(
                [('country_group_ids', '=', False)], limit=1)
            pl = pls and pls[0].id

        if not pl:
            prop = Property.get('property_product_pricelist', 'res.partner')
            pl = prop and prop[0].id

        if not pl:
            pls = self.env['product.pricelist'].search([], limit=1)
            pl = pls and pls[0].id

        return pl
