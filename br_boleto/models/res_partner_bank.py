# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    # Por motivos de falta de conhecimento este campo agora virou código
    # de beneficiario - Código Cnab virou código de Convênio
    codigo_convenio = fields.Char(u'Código de Beneficiário')
