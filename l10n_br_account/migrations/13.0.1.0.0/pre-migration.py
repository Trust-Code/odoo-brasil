from openupgradelib import openupgrade

_model_renames = [
    ('br_account.service.type', 'account.service.type'),
    ('product.fiscal.classification', 'account.ncm'),
    ('br_account.fiscal.category', 'product.fiscal.category'),
]

_table_renames = [
    ('br_account_service_type', 'account_service_type'),
    ('product_fiscal_classification', 'account_ncm'),
    ('br_account_fiscal_category', 'product_fiscal_category'),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_models(env.cr, _model_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
