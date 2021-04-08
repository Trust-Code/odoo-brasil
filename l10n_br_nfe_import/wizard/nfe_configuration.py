from odoo import api, fields, models
from odoo.exceptions import UserError


class WizardNFeConfiguration(models.TransientModel):
    _name = "wizard.nfe.configuration"

    eletronic_doc_id = fields.Many2one("eletronic.document")
    partner_id = fields.Many2one("res.partner", string="Parceiro")

    currency_id = fields.Many2one(related='eletronic_doc_id.currency_id')

    nfe_number = fields.Integer(related="eletronic_doc_id.numero")
    amount_total = fields.Monetary(related="eletronic_doc_id.valor_final")

    nfe_item_ids = fields.One2many('wizard.nfe.configuration.item', 'wizard_id')
    
    def action_confirm_items(self):
        for item in self.nfe_item_ids:
            if not item.product_id or not item.uom_id:
                raise UserError('Configure todos os produtos para continuar')
        
            item.eletronic_line_id.product_id = item.product_id.id
            item.eletronic_line_id.uom_id = item.uom_id.id
        
        return {
            "type": "ir.actions.act_window",
            "res_model": "eletronic.document",
            "view_mode": "tree,form",
            'view_type': 'form',
            'views': [[False, 'form']],
            "name": "Nota Fiscal Eletrônica",
            "res_id": self.eletronic_doc_id.id,
        }


class WizardNFeConfigurationItem(models.TransientModel):
    _name = "wizard.nfe.configuration.item"

    wizard_id = fields.Many2one('wizard.nfe.configuration')
    product_id = fields.Many2one("product.product")
    uom_id = fields.Many2one("uom.uom")
    
    eletronic_line_id = fields.Many2one("eletronic.document.line")
    currency_id = fields.Many2one(related='eletronic_line_id.currency_id')
    quantity = fields.Float(related='eletronic_line_id.quantidade')
    price_total = fields.Monetary(related="eletronic_line_id.valor_liquido")
    xml_product_code = fields.Char(related="eletronic_line_id.product_cprod", string="Cód.")
    xml_product_name = fields.Char(related="eletronic_line_id.product_xprod")
    xml_uom_code = fields.Char(related="eletronic_line_id.unidade_medida", string="Un.")
    xml_ncm_code = fields.Char(related="eletronic_line_id.ncm")
    xml_cfop = fields.Char(related="eletronic_line_id.cfop")
