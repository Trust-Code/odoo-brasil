import re
import requests
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
    sincronizado_ibpt = fields.Boolean(default=False)
    fonte_impostos = fields.Char(string="Fonte dos Impostos", size=100)

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
    sincronizado_ibpt = fields.Boolean(default=False)
    fonte_impostos = fields.Char(string="Fonte dos Impostos", size=100)

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

    def notify_account_users(self, message):
        partner = self.env['res.users'].browse(self.env.context['uid']).partner_id
        odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")

        channel_info = self.env['mail.channel'].channel_get([partner.id, odoobot_id], pin=True)
        channel = self.env['mail.channel'].browse(channel_info['id'])
        channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment", subtype="mail.mt_comment")

    def cron_sync_average_tax_rate(self):
        if not self.env.company.l10n_br_ibpt_api_token:
            message = "Você ainda não configurou o sistema para a lei de Olho no Imposto. " + \
                "Crie um token aqui: https://deolhonoimposto.ibpt.org.br/Site/PassoPasso " + \
                "E depois registre o mesmo em configurações da empresa. Após isto o sistema irá "+ \
                "sincronizar automaticamente as informações."
            self.notify_account_users(message)
            return

        headers = {
            "content-type": "application/json;",
        }

        products = self.env['product.template'].search(
            [('l10n_br_ncm_id.sincronizado_ibpt', '=', False)])

        for ncm in products.mapped('l10n_br_ncm_id'):
            url = 'https://apidoni.ibpt.org.br/api/v1/produtos'
            data = {
                'token': self.env.company.l10n_br_ibpt_api_token,
                'cnpj': re.sub('[^0-9]', '', self.env.company.l10n_br_cnpj_cpf or ''),
                'codigo': re.sub('[^0-9]', '', ncm.code or ''),
                'uf': self.env.company.state_id.code,
                'ex': 0,
                'descricao': '-----',
                'unidadeMedida': ncm.unidade_tributacao,
                'valor': 1,
                'gtin': '-',
            }
            response = requests.get(url, params=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            ncm.write({
                'federal_nacional': result['Nacional'],
                'federal_importado': result['Importado'],
                'estadual_imposto': result['Estadual'],
                'municipal_imposto': result['Municipal'],
                'fonte_impostos': result['Fonte'],
                'sincronizado_ibpt': True,
            })
            self.env.cr.commit()

        services = self.env['product.template'].search(
            [('service_type_id.sincronizado_ibpt', '=', False)])

        for ncm in services.mapped('service_type_id'):
            url = 'https://apidoni.ibpt.org.br/api/v1/servicos'
            data = {
                'token': self.env.company.l10n_br_ibpt_api_token,
                'cnpj': re.sub('[^0-9]', '', self.env.company.l10n_br_cnpj_cpf or ''),
                'codigo': re.sub('[^0-9]', '', ncm.code or ''),
                'uf': self.env.company.state_id.code,
                'descricao': '-----',
                'unidadeMedida': 'UN',
                'valor': 1,
            }
            response = requests.get(url, params=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            ncm.write({
                'federal_nacional': result['Nacional'],
                'federal_importado': result['Importado'],
                'estadual_imposto': result['Estadual'],
                'municipal_imposto': result['Municipal'],
                'fonte_impostos': result['Fonte'],
                'sincronizado_ibpt': True,
            })
            self.env.cr.commit()
