from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_br_tipo_ambiente = fields.Selection(
        [('producao', 'Produção'),
         ('homologacao', 'Homologação')], string="Ambiente", default="homologacao"
    )
    l10n_br_tax_regime = fields.Selection(
        [('simples', 'Simples Nacional'),
         ('presumido', 'Lucro Presumido'),
         ('real', 'Lucro Real')], string="Regime tributário")


    # NFS-e
    l10n_br_nfse_token_acess = fields.Char(string="Token de Acesso API", size=100)
    l10n_br_aedf = fields.Char(
        string="Número AEDF", size=10, help="Número de autorização para emissão de NFSe")
    l10n_br_client_id = fields.Char(string='Client Id', size=50)
    l10n_br_client_secret = fields.Char(string='Client Secret', size=50)
    l10n_br_user_password = fields.Char(string='Senha Acesso', size=50)

    l10n_br_cnae_main_id = fields.Many2one(
        'account.cnae', 'CNAE Primário')
    l10n_br_cnae_secondary_ids = fields.Many2many(
        'account.cnae', 'res_company_account_cnae',
        'company_id', 'cnae_id', 'CNAE Secundários')

    # NF-e
    l10n_br_accountant_id = fields.Many2one('res.partner', string="Contador")

    l10n_br_nfe_email_template = fields.Many2one(
        'mail.template', string="Template de Email para NFe")

    l10n_br_nfe_sequence = fields.Many2one(
        'ir.sequence', string="Sequência Numeracao NFe")
    l10n_br_nfe_service_sequence = fields.Many2one(
        'ir.sequence', string="Sequência Numeracao NFe de Servico")
    l10n_br_automated_weight = fields.Boolean(
        string="Calculo de peso automatizado"
    )

    l10n_br_cabecalho_danfe = fields.Selection(
        [
            ("vertical", "Modelo Vertical"),
            ("horizontal", "Modelo Horizontal"),
        ],
        string=u"Cabeçalho Danfe",
        default="vertical",
    )
    # NFC-e
    l10n_br_id_token_csc = fields.Char(string="Identificador do CSC")
    l10n_br_csc = fields.Char(string="Código de Segurança do Contribuinte")
    l10n_br_nfe_sinc = fields.Boolean(string="Aceita envio síncrono")

    # Responsavel Técnico
    l10n_br_id_token_csrt = fields.Char(string="Identificador do Responsavel Técnico")
    l10n_br_csrt = fields.Char(string="Código de Segurança do Responsavel Técnico")
    l10n_br_responsavel_tecnico_id = fields.Many2one(
        string="Responsável Técnico", comodel_name="res.partner")
    l10n_br_iest_ids = fields.One2many(
        'res.company.iest', 'company_id', string="Inscrições Estaduais ST")


class ResCompanyIest(models.Model):
    _name = 'res.company.iest'
    _description = "Inscrição Estadual do substituto tributário"

    name = fields.Char(string="Inscrição Estadual", required=True)
    state_id = fields.Many2one(
        'res.country.state', string="Estado", required=True)
    company_id = fields.Many2one(
        'res.company', string="Empresa", required=True)
