# © 2014 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class BrHrCbo(models.Model):
    _name = "br_hr.cbo"
    _description = "Brazilian Classification of Occupation"

    code = fields.Integer(string='Code', required=True)
    name = fields.Char('Name', size=255, required=True, translate=True)
