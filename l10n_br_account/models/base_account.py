from odoo import api, fields, models


class AccountServiceType(models.Model):
    _name = 'account.service.type'
    _description = 'Cadastro de Operações Fiscais de Serviço'

    code = fields.Char('Código', size=16, required=True)
    name = fields.Char('Descrição', size=256, required=True)
    parent_id = fields.Many2one(
        'account.service.type', 'Tipo de Serviço Pai')
    child_ids = fields.One2many(
        'account.service.type', 'parent_id',
        'Tipo de Serviço Filhos')
    internal_type = fields.Selection(
        [('view', 'Visualização'), ('normal', 'Normal')], 'Tipo Interno',
        required=True, default='normal')
    federal_nacional = fields.Float('Imposto Fed. Sobre Serviço Nacional')
    federal_importado = fields.Float('Imposto Fed. Sobre Serviço Importado')
    estadual_imposto = fields.Float('Imposto Estadual')
    municipal_imposto = fields.Float('Imposto Municipal')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result

