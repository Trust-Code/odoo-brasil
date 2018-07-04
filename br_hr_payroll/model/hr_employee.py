# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def get_accumulated_fgts(self):
        for item in self:
            fgts_positivo = self.env.cr.execute(
                """SELECT SUM(amount) FROM hr_payslip_line a
                   INNER JOIN hr_payslip b on a.slip_id = b.id
                   WHERE a.code='FGTS' AND b.credit_note=false""")
            fgts_positivo = self.env.cr.fetchone()
            fgts_negativo = self.env.cr.execute(
                """SELECT SUM(amount) FROM hr_payslip_line a
                   INNER JOIN hr_payslip b on a.slip_id = b.id
                   WHERE a.code='FGTS' AND b.credit_note=true""")
            fgts_negativo = self.env.cr.fetchone()
            item.accumulated_fgts = ((fgts_positivo[0] or 0) -
                                     (fgts_negativo[0] or 0))

    accumulated_fgts = fields.Float(u'FGTS Acumulado',
                                    compute=get_accumulated_fgts)
