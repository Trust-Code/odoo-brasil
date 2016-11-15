odoo.define('br_website_sale.address', function (require) {
"use strict";

var ajax = require('web.ajax');

$(document).ready(function () {
    var SPMaskBehavior = function(val) {
            return val.replace(/\D/g, '').length === 11 ?
                '(00) 00000-0000' :
                '(00) 0000-00009';
        },
        spOptions = {
            onKeyPress: function(val, e, field, options) {
                field.mask(SPMaskBehavior.apply({},
                    arguments), options);
            }
        };
    $('input[name="zip"]').mask('00000-000');
    $('input[name="cnpj_cpf"]').mask('000.000.000-00');
    $('input[name="phone"]').mask(SPMaskBehavior,
        spOptions);

    $('.oe_website_sale').each(function() {
        var oe_website_sale = this;

        $(oe_website_sale).on('change', "select[name='state_id']", function() {
            var vals = { 'state_id': $(this).val() };
            ajax.jsonRpc("/shop/get_cities", 'call', vals)
                .then(function(data) {
                    var selected = $('#input_city_id').val();
                    $('#select_city_id').find('option').remove().end();
                    $('#select_city_id').append('<option value="">Cidade...</option>');
                    $.each(data, function(i, item) {
                        $('#select_city_id').append($('<option>', {
                            value: item[0],
                            text: item[1],
                            selected: item[0]==selected?true:false,
                        }));
                    });
                });
            });
        $(oe_website_sale).find("select[name='state_id']").change();
    });


});

});
