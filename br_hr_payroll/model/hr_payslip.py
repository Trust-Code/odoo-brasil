# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from math import ceil
from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def week_of_month(self, dt):
        """ Returns the week of the month for the specified date.
        """

        first_day = dt.replace(day=1)

        dom = dt.day
        adjusted_dom = dom + first_day.weekday()

        return int(ceil(adjusted_dom/7.0))

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        if not contracts:
            return []
        self.env.cr.execute(
            "select sum(worked_hours) from hr_attendance \
            where check_in::date between %s and %s and employee_id = %s",
            (date_from, date_to, contracts[0].employee_id.id)
        )
        attendance_hours = self.env.cr.fetchone()[0]
        return [{
            'name': "Presenças Registradas",
            'code': 'FREQ',
            'amount': attendance_hours,
            'contract_id': contracts[0].id,
        }]

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self).get_worked_day_lines(
            contract_ids, date_from, date_to)
        employee = self.employee_id
        contract = self.env['hr.contract'].browse(
            self.get_contract(employee, date_from, date_to))
        if contract:
            leaves = self.env['hr.holidays'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('date_from', '>=', date_from),
                 ('date_to', '<=', date_to),
                 ('state', '=', 'validate'),
                 ('type', '=', 'remove')])
            dsr = {}
            for leave in leaves:
                # BUG: Fazer validação da falta
                if leave.holiday_status_id.name == 'Unpaid':
                    leave_start = fields.Datetime.from_string(leave.date_from)
                    dsr[self.week_of_month(leave_start)] = leave_start
            dsr_dict = {
                'name': "Descanso Semanal Remunerado",
                'sequence': 8,
                'code': 'DSR',
                'number_of_days': len(dsr),
                'contract_id': contract.id,
            }
            if dsr_dict['number_of_days'] != 0:
                res += [dsr_dict]
            return res
