
# from openupgradelib.openupgrade import rename_tables, rename_columns


def migrate(cr, version):
    cr.execute('CREATE TABLE res_city (LIKE res_state_city INCLUDING ALL);')
    cr.execute('INSERT INTO res_city SELECT * FROM res_state_city;')
    # rename_columns(cr, {'res_partner': [('city_id', 'temp_city_id')]})
    # rename_tables(cr, [('res_state_city', 'res_city')])
