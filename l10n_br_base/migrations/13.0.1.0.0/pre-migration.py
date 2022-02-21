from openupgradelib import openupgrade

_field_renames = [
    # Company
    ('res.company', 'res_company', 'nfe_a1_file', 'l10n_br_certificate'),
    ('res.company', 'res_company', 'nfe_a1_password', 'l10n_br_cert_password'),

    ('res.country', 'res_country', 'ibge_code', 'l10n_br_ibge_code'),
    ('res.country.state', 'res_country_state', 'ibge_code', 'l10n_br_ibge_code'),

]

@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)


