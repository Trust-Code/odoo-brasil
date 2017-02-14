# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    tipo_ambiente = fields.Selection([('1', u'Produção'),
                                      ('2', u'Homologação')],
                                     string="Ambiente NFe", default='2')

    cabecalho_danfe = fields.Selection([('vertical', 'Modelo Vertical'),
                                        ('horizontal', 'Modelo Horizontal')],
                                       string=u"Cabeçalho Danfe",
                                       default='vertical')

    nfe_email_template = fields.Many2one('mail.template',
                                         string="Template de Email para NFe")
