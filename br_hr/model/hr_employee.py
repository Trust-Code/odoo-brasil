# © 2014 KMEE (http://www.kmee.com.br)
# @author Rafael da Silva Lima <rafael.lima@kmee.com.br>
# @author Matheus Felix <matheus.felix@kmee.com.br>
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    @api.depends('dependent_ids')
    def _number_dependents(self):
        for item in self:
            item.no_of_dependent = \
                sum(1 if x.is_dependent else 0 for x in item.dependent_ids)
            item.no_of_dependent_health_plan = \
                sum(1 if x.use_health_plan else 0 for x in item.dependent_ids)

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
                    raise ValidationError(_("PIS/PASEP Inválido"))
                continue

            if c.isdigit():
                digits.append(int(c))
                continue

            raise ValidationError(_("PIS/PASEP Inválido"))
        if len(digits) != 11:
            raise ValidationError(_("PIS/PASEP Inválido"))

        height = [int(x) for x in "3298765432"]

        total = 0

        for i in range(10):
            total += digits[i] * height[i]

        rest = total % 11
        if rest != 0:
            rest = 11 - rest
        if rest != digits[10]:
            raise ValidationError(_("PIS/PASEP Inválido"))

    pis_pasep = fields.Char(u'PIS/PASEP', size=15)
    ctps = fields.Char('CTPS', help=u'Número da CTPS')
    ctps_series = fields.Char(u'Série')
    ctps_date = fields.Date(u'Data de emissão')
    creservist = fields.Char(u'Certificado de reservista')
    crresv_categ = fields.Char('Categoria')
    cr_categ = fields.Selection([('estagiario', u'Estagiário'),
                                 ('junior', u'Júnior'),
                                 ('pleno', 'Pleno'),
                                 ('senior', u'Sênior')],
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
    rg = fields.Char('RG', help=u'Número do RG')
    cpf = fields.Char(related='address_home_id.cnpj_cpf',
                      string='CPF')
    organ_exp = fields.Char(u"Orgão de expedição")
    rg_emission = fields.Date(u'Data de emissão')
    title_voter = fields.Char('Title', help=u'Número título')
    zone_voter = fields.Char('Zona')
    session_voter = fields.Char(u'Secção')
    driver_license = fields.Char('Carteira de motorista',
                                 help=u'Número da carteira de motorista')
    driver_categ = fields.Char('Categoria')
    father_name = fields.Char('Nome do Pai')
    mother_name = fields.Char(u'Nome da Mãe')
    validade = fields.Date('Validade')
    sindicate = fields.Char('Sindicato', help="Sigla do Sindicato")
    no_of_dependent = fields.Integer(u'Número de dependentes',
                                     compute=_number_dependents)
    no_of_dependent_health_plan = fields.Integer(u'Número de dependentes',
                                                 compute=_number_dependents)


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Employee\'s Dependents'

    @api.one
    @api.constrains('dependent_age')
    def _check_birth(self):
        dep_age = datetime.strptime(
            self.dependent_age, DEFAULT_SERVER_DATE_FORMAT)
        if dep_age.date() > datetime.now().date():
            raise ValidationError(_('Data de aniversário inválida'))
        return True

    employee_id = fields.Many2one('hr.employee', u'Funcionário')
    dependent_name = fields.Char('Nome', size=64, required=True,
                                 translate=True)
    dependent_age = fields.Date('Data de nascimento', required=True)
    dependent_type = fields.Char('Tipo', required=True)
    pension_benefits = fields.Float(
        u'% Pensão', help=u"Percentual a descontar de pensão alimenticia")
    is_dependent = fields.Boolean(u'É dependente', required=False)
    use_health_plan = fields.Boolean(u'Plano de saúde?', required=False)
