# -*- coding: utf-8 -*-
# © 2015 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    last_nsu_nfe = fields.Char(string="Último NSU usado", size=20, default='0')

    manifest_automation = fields.Selection(
        [('nenhuma', 'Nenhuma'),
         ('ciencia', 'Ciência Automática'),
         ('fatura', 'Registrar Fatura'),
         ('completa', 'Completa')], string="Automação Manifesto",
        help="Nenhuma - Nenhuma automação no processo é feita\n \
Ciência Automática - Todas as notas recebidas são baixadas automaticamente\n \
Registrar Fatura - Notas são baixadas e importadas automaticamente caso \
encontre o fornecedor.\n \
Completa - Todo o processo anterior é feito, caso não encontre o fornecedor o \
mesmo é criado")
