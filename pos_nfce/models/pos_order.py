# -*- coding: utf-8 -*-
from odoo import api, models
import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create_final_costumer(self, user_id):
        final_costumer = self.env['res.partner'].search(
            [('name', '=', 'Consumidor Final')]
        )
        if len(final_costumer) == 0:
            user = self.env['res.users'].search(
                [('id', '=', user_id['user_id'])]
            )
            final_costumer = self.env['res.partner'].create(dict(
                name='Consumidor Final',
                zip=user.company_id.partner_id.zip,
                street=user.company_id.partner_id.street,
                number=user.company_id.partner_id.number,
                district=user.company_id.partner_id.district,
                phone=user.company_id.partner_id.phone,
                country_id=user.company_id.partner_id.country_id.id,
                state_id=user.company_id.partner_id.state_id.id,
                city_id=user.company_id.partner_id.city_id.id,
                company_type='person',
                is_company=False,
                customer=True
            ))
        return final_costumer.id
