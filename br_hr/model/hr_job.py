# © 2014 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrJob(models.Model):
    _inherit = 'hr.job'

    cbo_id = fields.Many2one('br_hr.cbo', 'CBO')
