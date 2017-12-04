# -*- coding: utf-8 -*-
# © 2017 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class SimplesNacional(models.Model):
    _name = 'simples.nacional'

    company_id = fields.Many2one('res.company', string="Empresa")
    account_id = fields.Many2one('account.account', string='Conta Contábil')
    tax = fields.Float(string='Alíquota')
    deducao = fields.Float(string='Parcela Dedutiva')
    icms_percent = fields.Float(string='% de ICMS')
