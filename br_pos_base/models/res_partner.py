# © 2019 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_from_ui(self, partner):
        partner['is_company'] = True \
            if partner.get('is_company', '') == 'juridica' else False
        val = re.sub('[^0-9]', '', partner.get('cnpj_cpf', ''))
        if len(val) == 14:
            cnpj_cpf = "%s.%s.%s/%s-%s"\
                % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            partner['cnpj_cpf'] = cnpj_cpf
        elif not self.is_company and len(val) == 11:
            cnpj_cpf = "%s.%s.%s-%s"\
                % (val[0:3], val[3:6], val[6:9], val[9:11])
            partner['cnpj_cpf'] = cnpj_cpf
        return super(ResPartner, self).create_from_ui(partner)
