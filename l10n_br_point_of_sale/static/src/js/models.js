odoo.define('br_point_of_sale.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.partner', [
        'l10n_br_legal_name', 'l10n_br_cnpj_cpf', 'is_company', 'l10n_br_number', 
        'l10n_br_district', 'street2', 'state_id', 'city_id']);

    var _super_posmodel = models.PosModel.prototype;
    var _super_posorder = models.Order.prototype;

    models.Order = models.Order.extend({
        initialize: function(attributes, options){
            this.set({customerCpf: null});
            return _super_posorder.initialize.call(this, attributes, options);
        },
        export_as_JSON: function() {
            var vals = _super_posorder.export_as_JSON.call(this);
            vals["customer_cpf"] = this.get_client_cpf()
            return vals;
        },
        set_client_cpf: function(customerCpf){
            this.assert_editable();
            this.set('customerCpf', customerCpf);
        },
        get_client_cpf: function(){
            return this.get('customerCpf');
        },
    });

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.models.push({
                model: 'res.country.state',
                fields: ['name', 'country_id'],
                loaded: function (self, states) {
                    self.company.state = null;
                    self.states = states;
                }
            });
            this.models.push({
                model: 'res.city',
                fields: ['name', 'state_id'],
                loaded: function (self, cities) {
                    self.company.city = null;
                    self.cities = cities;
                }
            });
            // Inheritance
            return _super_posmodel.initialize.call(this, session, attributes);
        },
    });
});
