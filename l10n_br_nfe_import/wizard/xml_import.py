import base64
from lxml import objectify

from odoo import api, models, fields
from odoo.exceptions import UserError



class WizardXmlImport(models.TransientModel):
    _name = 'wizard.xml.import'

    state = fields.Selection([('ok', 'OK'), ('error', 'Erro')], default='ok')

    nfe_xml = fields.Binary('XML da NFe')
    skip_wrong_xml = fields.Boolean(
        string="Ignorar Xml com erro?", help="Se marcado vai ignorar os xmls \
        que estão com erro e importar o restante! Os xmls com erro serão \
        disponibilizados para download", default=True)

    already_imported = fields.Boolean(string="Xml já importado!")

    partner_id = fields.Many2one('res.partner', string="Parceiro")
    partner_data = fields.Char(string="Dados do parceiro")
    nfe_type = fields.Selection([('1', 'Entrada'), ('2', 'Saída')], string="Tipo de NF-e")
    total_products = fields.Integer(string="Qtd. de Produtos")
    amount_total = fields.Float(string='Total')
    
    create_partner = fields.Boolean("Cadastrar o parceiro?", default=True)

    @api.onchange('nfe_xml')
    def _onchange_nfe_xml(self):
        if self.nfe_xml:
            self._update_basic_info()
        else:
            self.already_imported = False

    def _update_basic_info(self):
        xml = base64.b64decode(self.nfe_xml)
        nfe = objectify.fromstring(xml)
        values = self.env['eletronic.document'].get_basic_info(nfe)
        self.update(values)
        
    def action_import_nfe(self):
        if not self.nfe_xml:
            raise UserError('Por favor, insira um arquivo de NFe.')
        self._update_basic_info()

        xml = base64.b64decode(self.nfe_xml)
        document = self.env['eletronic.document'].generate_eletronic_document(
            xml_nfe=xml, create_partner=self.create_partner)
        
        next_action = document.check_inconsistency_and_redirect()
        if next_action:
            return next_action

        return {
            "type": "ir.actions.act_window",
            "res_model": "eletronic.document",
            "view_mode": "tree,form",
            "name": "Notas Fiscais",
            "res_id": self.id,
            "domain": [("id", "=", document.id)]
        }


