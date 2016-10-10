# -*- coding: utf-8 -*-
# © 2009 Renato Lima - Akretion
# © 2014  KMEE - www.kmee.com.br
# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class BrAccountCFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _name = 'br_account.cfop'
    _description = 'CFOP'

    code = fields.Char(u'Código', size=4, required=True)
    name = fields.Char('Nome', size=256, required=True)
    small_name = fields.Char('Nome Reduzido', size=32, required=True)
    description = fields.Text(u'Descrição')
    type = fields.Selection([('input', u'Entrada'), ('output', 'Saída')],
                            'Tipo', required=True)
    parent_id = fields.Many2one(
        'br_account.cfop', 'CFOP Pai')
    child_ids = fields.One2many(
        'br_account.cfop', 'parent_id', 'CFOP Filhos')
    internal_type = fields.Selection(
        [('view', u'Visualização'), ('normal', 'Normal')],
        'Tipo Interno', required=True, default='normal')

    _sql_constraints = [
        ('br_account_cfop_code_uniq', 'unique (code)',
            u'Já existe um CFOP com esse código !')
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result


class BrAccountServiceType(models.Model):
    _name = 'br_account.service.type'
    _description = u'Cadastro de Operações Fiscais de Serviço'

    code = fields.Char(u'Código', size=16, required=True)
    name = fields.Char(u'Descrição', size=256, required=True)
    parent_id = fields.Many2one(
        'br_account.service.type', 'Tipo de Serviço Pai')
    child_ids = fields.One2many(
        'br_account.service.type', 'parent_id',
        u'Tipo de Serviço Filhos')
    internal_type = fields.Selection(
        [('view', u'Visualização'), ('normal', 'Normal')], 'Tipo Interno',
        required=True, default='normal')
    federal_nacional = fields.Float(u'Imposto Fed. Sobre Serviço Nacional')
    federal_importado = fields.Float(u'Imposto Fed. Sobre Serviço Importado')
    estadual_imposto = fields.Float(u'Imposto Estadual')
    municipal_imposto = fields.Float(u'Imposto Municipal')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s - %s" % (rec.code, rec.name or '')))
        return result


class BrAccountFiscalDocument(models.Model):
    _name = 'br_account.fiscal.document'
    _description = 'Tipo de Documento Fiscal'

    code = fields.Char(u'Codigo', size=8, required=True)
    name = fields.Char(u'Descrição', size=64)
    electronic = fields.Boolean(u'Eletrônico')


class BrAccountDocumentSerie(models.Model):
    _name = 'br_account.document.serie'
    _description = 'Serie de documentos fiscais'

    code = fields.Char(u'Código', size=3, required=True)
    name = fields.Char(u'Descrição', required=True)
    active = fields.Boolean('Ativo')
    fiscal_type = fields.Selection([('service', u'Serviço'),
                                    ('product', 'Produto')], 'Tipo Fiscal',
                                   default='service')
    fiscal_document_id = fields.Many2one('br_account.fiscal.document',
                                         'Documento Fiscal', required=True)
    company_id = fields.Many2one('res.company', 'Empresa',
                                 required=True)
    internal_sequence_id = fields.Many2one('ir.sequence',
                                           u'Sequência Interna')

    @api.model
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every
         new document serie """
        seq = {
            'name': vals['name'],
            'implementation': 'no_gap',
            'padding': 1,
            'number_increment': 1}
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.env['ir.sequence'].create(seq).id

    @api.model
    def create(self, vals):
        """ Overwrite method to create a new ir.sequence if
         this field is null """
        if not vals.get('internal_sequence_id'):
            vals.update({'internal_sequence_id': self._create_sequence(vals)})
        return super(BrAccountDocumentSerie, self).create(vals)


class BrAccountCNAE(models.Model):
    _name = 'br_account.cnae'
    _description = 'Cadastro de CNAE'

    code = fields.Char(u'Código', size=16, required=True)
    name = fields.Char(u'Descrição', size=64, required=True)
    version = fields.Char(u'Versão', size=16, required=True)
    parent_id = fields.Many2one('br_account.cnae', 'CNAE Pai')
    child_ids = fields.One2many(
        'br_account.cnae', 'parent_id', 'CNAEs Filhos')
    internal_type = fields.Selection(
        [('view', u'Visualização'), ('normal', 'Normal')],
        'Tipo Interno', required=True, default='normal')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class BrTaxDefinition(object):
    _name = 'br_tax.definition'

    tax_id = fields.Many2one('account.tax', string='Imposto', required=True)
    tax_domain = fields.Char('Tax Domain', store=True)
    tax_cst = fields.Char(u'Código de Imposto')
    company_id = fields.Many2one('res.company', string='Company',
                                 related='tax_id.company_id',
                                 store=True, readonly=True)
