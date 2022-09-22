odoo.define('br_website_sale.address', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');


    publicWidget.registry.BrWebsiteSale = publicWidget.Widget.extend({
        selector: '.l10n_br_public_contact_form',
        jsLibs: [
            '/l10n_br_website_sale/static/src/lib/jquery.mask.min.js'
        ],
        events: {
            'change #radioCompany': 'onChangeRadioCompany',
            'change #radioPerson': 'onChangeRadioCompany',
            'change #input_cnpj_cpf': 'onChangeCnpjCpf',
            'change #id_country': 'onChangeIdCountry',
            'change #select_state_id': 'onChangeSelectState',
            'change #input_zip': 'onChangeZip',

        },

        init: function (parent, options) {
            this._super(parent, options);
        },

        start: function() {
            if (this.$el.find("#radioCompany").length > 0) {
                let value = this.$el.find("#radioCompany")[0].checked;
                this.cnpj_cpf_mask(value);
                if(value) {
                    this.$el.find("label[for='input_cnpj_cpf']").html('CNPJ');
                }
            }
            this.zip_mask();

            var SPMaskBehavior = function (val) {
                return val.replace(/\D/g, '').length === 11 ? '(00) 00000-0000' :
                    '(00) 0000-00009';
            }
            var spOptions = {
                onKeyPress: function (val, e, field, options) {
                    field.mask(SPMaskBehavior.apply({},
                                arguments), options);
                }
            };

            $('input[name="phone"]').mask(SPMaskBehavior, spOptions);
            this.set_detault_state_city();
            return this._super.apply(this, arguments);
        },

        set_detault_state_city: function(){
            if(this.$el.find("#input_zip").val().length >= 8) {
                this.$el.find("#input_zip").trigger('change');
            } else {
                $("#id_country").change();
                let $state = $('#select_state_id');
                let default_state = $("#input_state_id").val();
                if(default_state) {
                    $state.val(default_state);
                    $state.change();
                    let $city = $('#select_city_id');
                    let default_city = $("#input_city_id").val();
                    $city.val(default_city);
                }
            }
        },

        cnpj_cpf_mask: function(company) {
            if (company) {
                this.$el.find('#input_cnpj_cpf').mask('00.000.000/0000-00');
            } else {
                this.$el.find('#input_cnpj_cpf').mask('000.000.000-00');
            }
        },

        zip_mask: function() {
            this.$el.find("#input_zip").mask("00000-000");
        },

        // EVENT HANDLERS

        onChangeRadioCompany: function(ev) {
            let $target = $(ev.target);
            if($target.val() == 'company') {
                this.$el.find("label[for=input_cnpj_cpf]").text("CNPJ")
                this.cnpj_cpf_mask(true);
            } else {
                this.$el.find("label[for=input_cnpj_cpf]").text("CPF")
                this.cnpj_cpf_mask(false);
            }
        },

        onChangeCnpjCpf: function() {
            if(this.$el.find("#radioCompany")[0].checked) {
                this.cnpj_cpf_mask(true);
            } else {
                this.cnpj_cpf_mask(false);
            }
        },

        onChangeIdCountry: function(ev) {
            var self = this;
            var vals = {country_id: $(ev.target).val()};
            ajax.jsonRpc("/shop/get_states", 'call', vals).then(function (data) {
                var selected = parseInt(self.$el.find('#input_state_id').val());
                $('#select_state_id').find('option').remove().end();
                $('#select_state_id').append(
                    '<option value="">Estado...</option>');
                $.each(data, function (i, item) {
                    $('#select_state_id').append($('<option>', {
                        value: item[0],
                        text: item[1],
                        selected: item[0]===selected?true:false,
                    }));
                });
                $('#select_state_id').trigger('change');
            });
        },

        onChangeSelectState: function(ev) {
            var self = this;
            var vals = { state_id: $(ev.target).val() };
            ajax.jsonRpc("/shop/get_cities", 'call', vals).then(function (data) {
                var selected = parseInt(self.$el.find('#input_city_id').val());
                $('#select_city_id').find('option').remove().end();
                $('#select_city_id').append(
                    '<option value="">Cidade...</option>');
                $.each(data, function (i, item) {
                    $('#select_city_id').append($('<option>', {
                        value: item[0],
                        text: item[1],
                        selected: item[0]===selected?true:false,
                    }));
                });
            });
        },

        disable_address_fields: function(disabled) {
            $('input[name="l10n_br_district"]').attr('disabled', disabled);
            $('input[name="street"]').attr('disabled', disabled);
            $('select[name="state_id"]').attr('disabled', disabled);
            $('select[name="city_id"]').attr('disabled', disabled);
        },

        onChangeZip: function(ev) {
            var self = this;
            var vals = {zip: $(ev.target).val()};
            this.disable_address_fields(true);
            ajax.jsonRpc("/shop/zip_search", 'call', vals)
                .then(function(data) {
                    if (data.sucesso) {
                        $('#input_state_id').val(data.state_id);
                        $('input[name="l10n_br_district"]').val(data.l10n_br_district);
                        $('input[name="street"]').val(data.street);
                        $('select[name="country_id"]').val(data.country_id);
                        $('select[name="country_id"]').change();
                        $('select[name="state_id"]').val(data.state_id);
                        $('select[name="state_id"]').change();
                        $('#input_city_id').val(data.city_id);
                        self.disable_address_fields(false);
                    } else {
                        alert('Nenhum cep encontrado');
                        self.disable_address_fields(false);
                    }
                }, () => self.disable_address_fields(false)
            );
        },
    });

    return publicWidget.registry.BrWebsiteSale;

});
