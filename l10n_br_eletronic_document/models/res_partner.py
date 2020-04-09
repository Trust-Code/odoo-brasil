from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_br_indicador_ie_dest = fields.Selection(
        [('1', '1 - Contribuinte ICMS'),
         ('2', '2 - Contribuinte isento de Inscrição no cadastro de \
                Contribuintes do ICMS'),
         ('9', '9 - Não Contribuinte, que pode ou não possuir Inscrição \
                Estadual no Cadastro de Contribuintes do ICMS')],
        string="Indicador IE", help="Caso não preencher este campo vai usar a \
        regra:\n9 - para pessoa física\n1 - para pessoa jurídica com IE \
        cadastrada\n2 - para pessoa jurídica sem IE cadastrada ou 9 \
        caso o estado de destino for AM, BA, CE, GO, MG, MS, MT, PE, RN, SP"
    )