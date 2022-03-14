from openupgradelib import openupgrade

_field_renames = [
    ('res.partner', 'res_partner', 'cnpj_cpf', 'l10n_br_cnpj_cpf'),
    ('res.partner', 'res_partner', 'legal_name', 'l10n_br_legal_name'),
    ('res.partner', 'res_partner', 'district', 'l10n_br_district'),
    ('res.partner', 'res_partner', 'number', 'l10n_br_number'),
    ('res.partner', 'res_partner', 'inscr_est', 'l10n_br_inscr_est'),
    ('res.partner', 'res_partner', 'suframa', 'l10n_br_suframa'),
    # Company
    ('res.company', 'res_company', 'cnpj_cpf', 'l10n_br_cnpj_cpf'),
    ('res.company', 'res_company', 'legal_name', 'l10n_br_legal_name'),
    ('res.company', 'res_company', 'district', 'l10n_br_district'),
    ('res.company', 'res_company', 'number', 'l10n_br_number'),
    ('res.company', 'res_company', 'inscr_est', 'l10n_br_inscr_est'),
    ('res.company', 'res_company', 'suframa', 'l10n_br_suframa'),
]

@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
