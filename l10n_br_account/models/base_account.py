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


class AccountNcm(models.Model):
    _name = 'account.ncm'
    _description = 'Classificações Fiscais (NCM)'

    code = fields.Char(string="Código", size=14)
    category = fields.Char(string="Categoria", size=14)
    name = fields.Char(string="Nome", size=300)
    company_id = fields.Many2one('res.company', string="Empresa")
    unidade_tributacao = fields.Char(string="Unidade Tributável", size=4)
    descricao_unidade = fields.Char(string="Descrição Unidade", size=20)
    cest = fields.Char(string="CEST", size=10,
                       help="Código Especificador da Substituição Tributária")
    federal_nacional = fields.Float('Imposto Fed. Sobre Produto Nacional')
    federal_importado = fields.Float('Imposto Fed. Sobre Produto Importado')
    estadual_imposto = fields.Float('Imposto Estadual')
    municipal_imposto = fields.Float('Imposto Municipal')

    # IPI
    classe_enquadramento = fields.Char(string="Classe Enquadr.", size=5)
    codigo_enquadramento = fields.Char(
        string="Cód. Enquadramento", size=3, default='999')

    active = fields.Boolean(default=True, string='Ativo')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result
