from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    def _get_company_address_fields(self, partner):
        vals = super(ResCompany, self)._get_company_address_fields(partner)
        vals.update({
            'l10n_br_cnpj_cpf': partner.l10n_br_cnpj_cpf,
            'l10n_br_legal_name': partner.l10n_br_legal_name,
            'l10n_br_district': partner.l10n_br_district,
            'l10n_br_number': partner.l10n_br_number,
            'l10n_br_inscr_est': partner.l10n_br_inscr_est,
            'l10n_br_inscr_mun': partner.l10n_br_inscr_mun,
            'l10n_br_suframa': partner.l10n_br_suframa,
            'city_id': partner.city_id,
        })
        return vals
    
    l10n_br_cnpj_cpf = fields.Char(string='CNPJ', compute='_compute_address', inverse='_inverse_cnpj_cpf')
    l10n_br_legal_name = fields.Char(string="Razão Social", compute='_compute_address', inverse='_inverse_legal_name')
    l10n_br_district = fields.Char(string="Bairro", compute='_compute_address', inverse='_inverse_district')
    l10n_br_number = fields.Char(string="Número", compute='_compute_address', inverse='_inverse_number')
    l10n_br_inscr_est = fields.Char(string="Inscr. Estadual", compute='_compute_address', inverse='_inverse_inscr_est')
    l10n_br_inscr_mun = fields.Char(string="Inscr. Municipal", compute='_compute_address', inverse='_inverse_inscr_mun')
    l10n_br_suframa = fields.Char(string="Suframa", compute='_compute_address', inverse='_inverse_cnpj_cpf')
    city_id = fields.Many2one('res.city', compute='_compute_address', inverse='_inverse_cnpj_cpf', string="Cidade")
    
    def _inverse_cnpj_cpf(self):
        for company in self:
            company.partner_id.l10n_br_cnpj_cpf = company.l10n_br_cnpj_cpf

    def _inverse_legal_name(self):
        for company in self:
            company.partner_id.l10n_br_legal_name = company.l10n_br_legal_name

    def _inverse_district(self):
        for company in self:
            company.partner_id.l10n_br_district = company.l10n_br_district

    def _inverse_number(self):
        for company in self:
            company.partner_id.l10n_br_number = company.l10n_br_number
  
    def _inverse_inscr_est(self):
        for company in self:
            company.partner_id.l10n_br_inscr_est = company.l10n_br_inscr_est
            
    def _inverse_inscr_mun(self):
        for company in self:
            company.partner_id.l10n_br_inscr_mun = company.l10n_br_inscr_mun
            
    def _inverse_suframa(self):
        for company in self:
            company.partner_id.l10n_br_suframa = company.l10n_br_suframa

    def _inverse_city_id(self):
        for company in self:
            company.partner_id.city_id = company.city_id