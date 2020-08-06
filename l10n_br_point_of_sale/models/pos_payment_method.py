from odoo import models, fields


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    metodo_pagamento = fields.Selection(
        [
            ("01", "Dinheiro"),
            ("02", "Cheque"),
            ("03", "Cartão de Crédito"),
            ("04", "Cartão de Débito"),
            ("05", "Crédito Loja"),
            ("10", "Vale Alimentação"),
            ("11", "Vale Refeição"),
            ("12", "Vale Presente"),
            ("13", "Vale Combustível"),
            ("15", "Boleto Bancário"),
            ("90", "Sem pagamento"),
            ("99", "Outros"),
        ],
        string="Forma de Pagamento",
        default="01",
    )
