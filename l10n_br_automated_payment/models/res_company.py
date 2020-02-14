# © 2018 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    iugu_api_token = fields.Char(string="IUGU Api Token", size=60)
    iugu_url_base = fields.Char(string="IUGU URL")
