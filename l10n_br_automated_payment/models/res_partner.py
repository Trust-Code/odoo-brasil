# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

import re
import iugu
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    iugu_id = fields.Char(string="ID Iugu", size=60)

    @api.multi
    def action_synchronize_iugu(self):
        for partner in self:
            token = self.env.user.company_id.iugu_api_token
            iugu.config(token=token)

            iugu_customer_api = iugu.Customer()
            commercial_part = partner.commercial_partner_id
            # TODO Validar telefone e passar
            vals = {
                'email': partner.email,
                'name': commercial_part.legal_name or commercial_part.name,
                'notes': commercial_part.comment or '',
                'cpf_cnpj': commercial_part.cnpj_cpf,
                'zip_code': re.sub('[^0-9]', '', commercial_part.zip or ''),
                'number': commercial_part.number,
                'street': commercial_part.street,
                'city': commercial_part.city_id.name,
                'state': commercial_part.state_id.code,
                'district': commercial_part.district or '',
                'complement': commercial_part.street2 or '',
            }
            if not partner.iugu_id:
                data = iugu_customer_api.create(vals)
                if "errors" in data:
                    msg = "\n".join(
                        ["A integração com IUGU retornou os seguintes erros"] +
                        ["Field: %s %s" % (x[0], x[1][0])
                         for x in data['errors'].items()])
                    raise UserError(msg)
                partner.iugu_id = data['id']
            else:
                iugu_customer_api.change(partner.iugu_id, vals)
