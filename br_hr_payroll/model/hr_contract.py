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

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def _get_worked_days(self):  # TODO Fazer validação se este número de
                                # dias está certo
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

    value_va = fields.Float(u'Vale Alimentação', help=u'Valor diário')
    percent_va = fields.Float(u'% Vale Alimentação',
                              help=u'Percentagem descontada ao final do mês')
    value_vr = fields.Float(u'Vale Refeição', help=u'Valor diário')
    percent_vr = fields.Float(u"% Vale Refeição",
                              help=u'Percentual descontado ao fim do mês')
    workeddays = fields.Float(compute=_get_worked_days,
                              string="Dias trabalhados")
    transportation_voucher = fields.Float(
        'Vale Transporte', help=u'Valor diário')
    percent_transportation = fields.Float(
        '% Vale Transporte',
        help=u'Percentual descontado ao fim do mês')
    health_insurance = fields.Float(
        u'Plano de saúde', help=u'Valor mensal do plano de saúde')
    health_insurance_dependent = fields.Float(
        u'Plano de Saúde de Dependentes',
        help=u'Plano de Saúde para Cônjugue e Dependentes')
    calc_date = fields.Boolean(compute=_check_date, string="Calcular data")
    ir_value = fields.Float(string="Valor IR")
