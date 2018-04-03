# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    regime_tributacao = fields.Selection(
        [('1', 'Microempresa Municipal'),
         ('2', 'Estimativa'),
         ('3', 'Sociedade de profissionais'),
         ('4', 'Cooperativa'),
         ('5', 'Microempresário individual (MEI)'),
         ('6', 'Microempresário e empresa de pequeno porte')],
        string="Regime Tributação")
