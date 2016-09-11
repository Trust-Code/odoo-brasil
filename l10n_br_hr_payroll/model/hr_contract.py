# -*- encoding: utf-8 -*-
##############################################################################
#
#    Brazillian Human Resources Payroll module for OpenERP
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Matheus Felix <matheus.felix@kmee.com.br>
#            Rafael da Silva Lima <rafael.lima@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

from odoo import api, fields, models
from odoo.tools.translate import _
import odoo.addons.decimal_precision as dp


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def _get_wage_ir(self): # TODO Acho que esse valor de IR deve ter uma tabela de faixa de valores, não pode ser fixo
        for item in self:
            obj_employee = self.env['hr.employee']
            employee_ids = obj_employee.search(
                [('contract_ids.id', '=', item.id)])
            for employee in employee_ids:
                for contract in employee.contract_ids:
                    INSS =(-482.93 if ((contract.wage) >= 4390.25) else -((contract.wage) * 0.11) if ((contract.wage) >= 2195.13) and ((contract.wage) <= 4390.24) else -((contract.wage) * 0.09) if ((contract.wage) >= 1317.08) and ((contract.wage) <= 2195.12) else -((contract.wage) * 0.08))
                    lane = (contract.wage - employee.no_of_dependent + INSS)
                    first_lane = (-(0.275*(lane) - 826.15))
                    l1 = Decimal(str(first_lane))
                    lane1 = l1.quantize(Decimal('1.10'), rounding=ROUND_DOWN)
                    option_one = float(lane1)
                    second_lane = (-(0.225*(lane) - 602.96))
                    l2 = Decimal(str(second_lane))
                    lane2 = l2.quantize(Decimal('1.10'), rounding=ROUND_DOWN)
                    option_two = float(lane2)
                    third_lane = (-(0.150*(lane) - 335.03))
                    l3 = Decimal(str(third_lane))
                    lane3 = l3.quantize(Decimal('1.10'), rounding=ROUND_DOWN)
                    option_three = float(lane3)
                    fourth_lane = (-(0.075*(lane) - 134.08))
                    l4 = Decimal(str(fourth_lane))
                    lane4 = l4.quantize(Decimal('1.10'), rounding=ROUND_DOWN)
                    option_four = float(lane4)
                    if (lane >= 4463.81):
                        item.ir_value = option_one
                    elif (lane <= 4463.80) and (lane >= 3572.44):
                        item.ir_value = option_two
                    elif (lane <= 3572.43) and (lane >= 2679.30):
                        item.ir_value = option_three
                    elif (lane <= 2679.29) and (lane >= 1787.78):
                        item.ir_value = option_four
                    else:
                        return 0

    @api.multi
    def _get_worked_days(self): #TODO Fazer validação se este número de dias está certo
        for item in self:
            item.workeddays = 22

    @api.multi
    def _check_date(self):
        for item in self:
            comp_date_from = time.strftime('%Y-04-01')
            comp_date_to = time.strftime('%Y-02-28')
            obj_payslip = self.env['hr.payslip']
            payslip_ids = obj_payslip.search(
                [('contract_id', '=', item.id),
                 ('date_from', '<', comp_date_from),
                 ('date_to', '>', comp_date_to)])
            if payslip_ids:
                item.calc_date = True
            else:
                item.calc_date = False

    @api.one
    @api.constrains('value_va', 'value_vr')
    def _check_voucher(self):
        if self.env.user.company_id.check_benefits:
            return True
        else:
            if self.value_va != 0 and self.value_vr != 0:
                raise ValidationError(
                    'A configuração da empresa não permite vale alimentação e refeição simultaneamente')

    value_va = fields.Float('Vale alimentação', help='Valor diário')
    value_vr = fields.Float('Vale Refeição', help='Valor diário')
    workeddays = fields.Float(compute=_get_worked_days,
                              string="Dias trabalhados")
    transportation_voucher = fields.Float(
        'Vale Transporte', help='Valor diário')
    health_insurance = fields.Float(
        'Plano de saúde', help='Valor mensal do plano de saúde')
    health_insurance_dependent = fields.Float(
        'Dependent Health Plan', help='Health Plan for Spouse and Dependents')
    calc_date = fields.Boolean(compute=_check_date, string="Calcular data")
    ir_value = fields.Float(compute=_get_wage_ir,
                            digits_compute=dp.get_precision('Payroll'),
                            string="Valor IR")
