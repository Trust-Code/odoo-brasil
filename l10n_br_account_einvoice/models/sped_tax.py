# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2016 TrustCode - www.trustcode.com.br                         #
#              Danimar Ribeiro <danimaribeiro@gmail.com>                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

from openerp import api, fields, models


class SpedTaxIcms(models.Model):
    _name = 'sped.tax.icms'

    @api.multi
    def name_get(self):
        return [(rec.id, u"{0} {1}% CST {2} R$ {3}".format(
                rec.name, rec.aliquota,
                rec.cst, rec.valor)
         ) for rec in self]

    name = fields.Char(u'Nome', size=20)
    origem = fields.Selection(
        [('0', '0 - Nacional'),
         ('1', '1 - Estrangeira - Importação direta'),
         ('2', '2 - Estrangeira - Adquirida no mercado interno'),
         ('3', '3 - Nacional, mercadoria ou bem com Conteúdo de Importação \
superior a 40% \e inferior ou igual a 70%'),
         ('4', '4 - Nacional, cuja produção tenha sido feita em conformidade \
com os processos produtivos básicos de que tratam as \
legislações citadas nos Ajustes'),
         ('5', '5 - Nacional, mercadoria ou bem com Conteúdo de Importação \
inferior ou igual a 40%'),
         ('6', '6 - Estrangeira - Importação direta, sem similar nacional, \
constante em lista da CAMEX e gás natural'),
         ('7', '7 - Estrangeira - Adquirida no mercado interno, sem similar \
nacional, constante lista CAMEX e gás natural'),
         ('8', '8 - Nacional, mercadoria ou bem com Conteúdo de Importação \
superior a 70%')],
        u'Origem da mercadoria')
    cst = fields.Selection(
     [
      ('00', '00 - Tributada Integralmente'),
      ('10', '10 - Tributada com ICMS ST'),
      ('20', '20 - Com redução de base de cálculo'),
      ('30', '30 - Isenta ou não tributada e com cobrança do ICMS por \
substituição tributária'),
      ('40', '40 - Isenta'),
      ('41', '41 - Não tributada'),
      ('50', '50 - Suspensão'),
      ('51', '51 - Diferimento'),
      ('60', '60 - ICMS cobrado anteriormente por substituição tributária'),
      ('70', '70 - Com redução de base de cálculo e cobrança do ICMS por \
substituição tributária'),
      ('90', '90 - Outros')],
     u'Situação tributária do ICMS')
    aliquota = fields.Float(u'Alíquota')
    modalidade_BC = fields.Selection(
        [('0', '0 - Margem Valor Agregado (%)'),
         ('1', '1 - Pauta (Valor)'),
         ('2', '2 - Preço Tabelado Máx. (valor)'),
         ('3', '3 - Valor da operação')],
        u'Modalidade de determinação da BC do ICMS')
    base_calculo = fields.Float(u'Base de cálculo')
    percentual_reducao_bc = fields.Float(u'% Redução Base')
    valor = fields.Float(u'Valor Total')

    percentual_mva = fields.Float(u'% MVA')
    aliquota_st = fields.Float(u'Alíquota')
    base_calculo_st = fields.Float(u'Base de cálculo')
    percentual_reducao_bc_st = fields.Float(u'% Redução Base')
    valor_st = fields.Float(u'Valor Total')

    percentual_diferimento = fields.Float(u'% Diferimento')
    valor_diferido = fields.Float(u'Valor Diferido')

    motivo_desoneracao = fields.Float(u'Motivo Desoneração')
    valor_desonerado = fields.Float(u'Valor Desonerado')


class SpedTaxIpi(models.Model):
    _name = 'sped.tax.ipi'

    name = fields.Char(u'Nome', size=20)

    classe_enquadramento = fields.Char(u'Classe enquadramento', size=5)
    codigo_enquadramento = fields.Char(u'Código enquadramento', size=4)
    cst = fields.Selection([('00', 'Tributada Integralmente'),
                            ('01', 'Tributada com ICMS ST')],
                           u'Situação tributária do ICMS')
    aliquota = fields.Float(u'Alíquota')
    base_calculo = fields.Float(u'Base de cálculo')
    percentual_reducao_bc = fields.Float(u'% Redução Base')
    valor = fields.Float(u'Valor Total')


class SpedTaxII(models.Model):
    _name = 'sped.tax.ii'

    name = fields.Char(u'Nome', size=20)
    base_calculo = fields.Float(u'Base de cálculo')
    valor_despesas = fields.Float(u'Despesas aduaneiras')
    valor_ii = fields.Float(u'Imposto de importação')
    valor_iof = fields.Float(u'IOF')


class SpedTaxPis(models.Model):
    _name = 'sped.tax.pis'

    name = fields.Char(u'Nome', size=20)
    cst = fields.Selection([('00', 'Tributada Integralmente'),
                            ('01', 'Tributada com ICMS ST')],
                           u'Situação tributária do ICMS')
    aliquota = fields.Float(u'Alíquota')
    base_calculo = fields.Float(u'Base de cálculo')
    valor = fields.Float(u'Valor Total')


class SpedTaxCofins(models.Model):
    _name = 'sped.tax.cofins'

    name = fields.Char(u'Nome', size=20)
    cst = fields.Selection([('00', 'Tributada Integralmente'),
                            ('01', 'Tributada com ICMS ST')],
                           u'Situação tributária do ICMS')
    aliquota = fields.Float(u'Alíquota')
    base_calculo = fields.Float(u'Base de cálculo')
    valor = fields.Float(u'Valor Total')


class SpedTaxIssqn(models.Model):
    _name = 'sped.tax.issqn'

    name = fields.Char(u'Nome', size=20)
    codigo = fields.Char(u'Código', size=10)
    aliquota = fields.Float(u'Alíquota')
    base_calculo = fields.Float(u'Base de cálculo')
    valor = fields.Float(u'Valor Total')
    valor_retencao = fields.Float(u'Valor retenção')


class SpedTaxCsll(models.Model):
    _name = 'sped.tax.csll'

    name = fields.Char(u'Nome', size=20)
    aliquota = fields.Float(u'Alíquota')
    base_calculo = fields.Float(u'Base de cálculo')
    valor = fields.Float(u'Valor Total')


class SpedTaxIrrf(models.Model):
    _name = 'sped.tax.irrf'

    name = fields.Char(u'Nome', size=20)
    aliquota = fields.Float(u'Alíquota')
    base_calculo = fields.Float(u'Base de cálculo')
    valor = fields.Float(u'Valor Total')


class SpedTaxInss(models.Model):
    _name = 'sped.tax.inss'

    name = fields.Char(u'Nome', size=20)
    aliquota = fields.Float(u'Alíquota')
    base_calculo = fields.Float(u'Base de cálculo')
    valor = fields.Float(u'Valor Total')
