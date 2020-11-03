odoo.define('br_point_of_sale.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var _super_posmodel = models.PosModel.prototype;
    var _super_posorder = models.Order.prototype;

    models.Order = models.Order.extend({
        initialize: function(attributes, options){
            this.set({customerCpf: null});
            return _super_posorder.initialize.call(this, attributes, options);
        },
        export_as_JSON: function() {
            var vals = _super_posorder.export_as_JSON.call(this);
            vals["customer_cpf"] = this.get_client_cpf();
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
            // Partner Fields
            var partner_model = _.find(this.models, function(model){
                return model.model === 'res.partner';
            });
            partner_model.fields.push('legal_name');
            partner_model.fields.push('cnpj_cpf');
            partner_model.fields.push('is_company');
            partner_model.fields.push('number');
            partner_model.fields.push('district');
            partner_model.fields.push('street2');
            partner_model.fields.push('state_id');
            partner_model.fields.push('city_id');

            this.models.push({
                model: 'res.country.state',
                fields: ['name', 'country_id'],
                loaded: function (self, states) {
                    self.company.state = null;
                    self.states = states;
                }
            });
            this.models.push({
                model: 'res.state.city',
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
