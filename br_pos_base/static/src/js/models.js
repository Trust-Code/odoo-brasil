odoo.define('br_point_of_sale.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.partner', [
      'legal_name', 'cnpj_cpf', 'is_company', 'number', 'district',
      'street2', 'state_id', 'city_id']);

    models.load_models({
        model: 'res.country.state',
        fields: ['name', 'country_id'],
        loaded: function (self, states) {
            self.company.state = null;
            self.states = states;
        }
    });

    models.load_models({
        model: 'res.state.city',
        fields: ['name', 'state_id'],
        loaded: function (self, cities) {
            self.company.city = null;
            self.cities = cities;
        }
    });
});
