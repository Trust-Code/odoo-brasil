odoo.define('br_pos_base.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.partner', [
        'legal_name', 'cnpj_cpf', 'is_company', 'number', 'district',
        'street2', 'state_id', 'city_id']);
});
