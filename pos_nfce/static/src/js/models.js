odoo.define('pos_nfce.models', function (require) {
    "use strict";
    var pos_model = require('point_of_sale.models');
    var fields = [
        'legal_name', 'cnpj_cpf', 'number',
        'district', 'city', 'state_id',
    ];
    pos_model.load_fields("res.company", fields);
    pos_model.Orderline = pos_model.Orderline.extend({
        get_total: function(){
            return this.quantity * this.priceWithTax;
        },
    });
});