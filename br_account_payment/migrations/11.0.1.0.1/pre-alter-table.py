

def migrate(cr, version):
    # Alter table name
    cr.execute('ALTER TABLE payment_mode RENAME TO l10n_br_payment_mode;')
