from openupgradelib import openupgrade

_model_renames = [
    ('invoice.eletronic', 'eletronic.document'),
    ('invoice.eletronic.item', 'eletronic.document.line'),
    ('br_account.cfop', 'nfe.cfop'),
    ('br_account.cnae', 'account.cnae'),
    ('br_account.import.declaration', 'nfe.import.declaration'),
    ('br_account.import.declaration', 'nfe.import.declaration.line'),
    ('br_account.fiscal.observation', 'nfe.fiscal.observation'),
]

_table_renames = [
    ('invoice_eletronic', 'eletronic_document'),
    ('invoice_eletronic_item', 'eletronic_document_line'),
    ('br_account_cfop', 'nfe_cfop'),
    ('br_account_cnae', 'account_cnae'),
    ('br_account_import_declaration', 'nfe_import_declaration'),
    ('br_account_import_declaration_line', 'nfe_import_declaration_line'),
    ('br_account_fiscal_observation', 'nfe_fiscal_observation'),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(env.cr, _model_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
    env.cr.execute("update ir_model_data set module = 'l10n_br_eletronic_document' where name like 'cfop_%' and model = 'nfe.cfop'")
    env.cr.execute("update ir_model_data set module = 'l10n_br_eletronic_document' where name like 'l10n_br_cnae%' and model = 'account.cnae'")
    env.cr.execute("update ir_model_data set module = 'l10n_br_eletronic_document' where name like 'service_type_%' and model = 'account.service.type'")
