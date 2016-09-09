# -*- coding: utf-8 -*-
# © 2014 KMEE (http://www.kmee.com.br)
# @author Rafael da Silva Lima <rafael.lima@kmee.com.br>
# @author Matheus Felix <matheus.felix@kmee.com.br>
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from datetime import datetime

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _get_dependents(self):
        for employee in self:
            dep_env = self.env['hr.employee.dependent']
            dep_ids = dep_env.search(
                [('employee_id', '=', employee.id),
                 ('dependent_verification', '=', True)])
            if dep_ids:
                employee.n_dependent = len(dep_ids)*179.71
                # TODO Estranho multiplicar isto aqui
            else:
                employee.n_dependent = 0

    @api.one
    @api.constrains('pis_pasep')
    def _validate_pis_pasep(self):
        if not self.pis_pasep:
            return True

        digits = []
        for c in self.pis_pasep:
            if c == '.' or c == ' ' or c == '\t':
                continue

            if c == '-':
                if len(digits) != 10:
                    raise ValidationError(u"PIS/PASEP Inválido")
                continue

            if c.isdigit():
                digits.append(int(c))
                continue

            raise ValidationError(u"PIS/PASEP Inválido")
        if len(digits) != 11:
            raise ValidationError(u"PIS/PASEP Inválido")

        height = [int(x) for x in "3298765432"]

        total = 0

        for i in range(10):
            total += digits[i] * height[i]

        rest = total % 11
        if rest != 0:
            rest = 11 - rest
        if rest != digits[10]:
            raise ValidationError(u"PIS/PASEP Inválido")

    check_cpf = fields.Boolean('Verificar CPF', default=True)
    pis_pasep = fields.Char(u'PIS/PASEP', size=15)
    ctps = fields.Char('CTPS', help='Número da CTPS')
    ctps_series = fields.Char('Série')
    ctps_date = fields.Date('Data de emissão')
    creservist = fields.Char('Certificado de reservista')
    crresv_categ = fields.Char('Categoria')
    cr_categ = fields.Selection([('estagiario', u'Estagiário'),
                                 ('junior', 'Júnior'),
                                 ('pleno', 'Pleno'),
                                 ('senior', 'Senior')],
                                string='Categoria')
    ginstru = fields.Selection(
        [('fundamental_incompleto', 'Basic Education incomplete'),
         ('fundamental', 'Basic Education complete'),
         ('medio_incompleto', 'High School incomplete'),
         ('medio', 'High School complete'),
         ('superior_incompleto', 'College Degree incomplete'),
         ('superior', 'College Degree complete'),
         ('mestrado', 'Master'),
         ('doutorado', 'PhD')],
        string='Schooling', help="Select Education")
    have_dependent = fields.Boolean("Possui dependentes")
    dependent_ids = fields.One2many('hr.employee.dependent',
                                    'employee_id', 'Dependentes')
    rg = fields.Char('RG', help='Número do RG')
    cpf = fields.Char(related='address_home_id.cnpj_cpf',
                      string='CPF', required=True)
    organ_exp = fields.Char("Orgão de expedição")
    rg_emission = fields.Date('Data de emissão')
    title_voter = fields.Char('Title', help='Número título')
    zone_voter = fields.Char('Zona')
    session_voter = fields.Char('Secção')
    driver_license = fields.Char('Carteira de motorista',
                                 help='Número da carteira de motorista')
    driver_categ = fields.Char('Categoria')
    father_name = fields.Char('Nome do Pai')
    mother_name = fields.Char('Nome da Mãe')
    validade = fields.Date('Validade')
    sindicate = fields.Char('Sindicato', help="Sigla do Sindicato")
    n_dependent = fields.Float(string="Dependentes", compute=_get_dependents,
                               type="float",
                               digits_compute=dp.get_precision('Payroll'))


    #TODO Remover se não necessário
    def onchange_user(self):
        res = super(HrEmployee, self).onchange_user(
            cr, uid, ids, user_id, context)

        obj_partner = self.pool.get('res.partner')
        partner_id = obj_partner.search(
            cr, uid, [('user_ids', '=', user_id)])[0]
        partner = obj_partner.browse(cr, uid, partner_id)

        res['value'].update({'address_home_id': partner.id,
                             'cpf': partner.cnpj_cpf})
        return res


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Employee\'s Dependents'

    @api.one
    @api.constrains('dependent_age')
    def _check_birth(self, cr, uid, ids, context=None):
        dep_age = datetime.strptime(
            self.dependent_age, DEFAULT_SERVER_DATE_FORMAT)
        if dep_age.date() > datetime.now().date():
            raise ValidationError(u'Data de aniversário inválida')
        return True

    employee_id = fields.Many2one('hr.employee', 'Funcionário')
    dependent_name = fields.Char('Nome', size=64, required=True,
                                 translate=True)
    dependent_age = fields.Date('Data de nascimento', required=True)
    dependent_type = fields.Char('Tipo', required=True)
    pension_benefits = fields.Float('Salário familia')
    dependent_verification = fields.Boolean('É dependente', required=False)
    health_verification = fields.Boolean('Plano de saúde?', required=False)
