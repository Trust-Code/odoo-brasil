from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    last_nsu_nfe = fields.Char("Último NSU usado", size=20, default='0')

    manifest_automation = fields.Boolean(
        string="Ciência da operação", help="Quando marcado, executa a\
        ciência da operação e realiza o download das respectivas NF-e's.")
    partner_automation = fields.Boolean(
        string="Cadastra parceiro", help="Quando marcado, cadastra\
        automaticamente o parceiro caso o mesmo não na exista.")
    invoice_automation = fields.Boolean(
        string="Registra fatura", help="Quando marcado, cria uma nova fatura\
        baseada nas informações da NF-e importada.")
    tax_automation = fields.Boolean(
        string="Cadastra impostos", help="Quando marcado, cria um imposto\
        com uma nova aliquota, caso a mesma não exista.")
    supplierinfo_automation = fields.Boolean(
        string="Cadastra produto do parceiro", help="Quando marcado, cria\
        cria um novo produto do parceiro, baseado nas informações da ordem de\
        compras informada na NF-e.")

    @api.onchange('partner_automation', 'invoice_automation', 'tax_automation',
                  'supplierinfo_automation')
    def _set_manifest_automation(self):
        if not self.manifest_automation and self.partner_automation:
            self.manifest_automation = True

        if not self.manifest_automation and self.invoice_automation:
            self.manifest_automation = True

        if not self.manifest_automation and self.tax_automation:
            self.manifest_automation = True

        if not self.manifest_automation and self.supplierinfo_automation:
            self.manifest_automation = True

    @api.onchange('tax_automation', 'supplierinfo_automation')
    def _set_invoice_automation(self):
        if not self.invoice_automation and self.tax_automation:
            self.invoice_automation = True

        if not self.invoice_automation and self.supplierinfo_automation:
            self.invoice_automation = True
