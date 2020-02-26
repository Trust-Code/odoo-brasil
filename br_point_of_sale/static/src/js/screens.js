odoo.define('br_point_of_sale.screens', function (require) {
    "use strict";

    var pos_screens = require('point_of_sale.screens');

    pos_screens.PaymentScreenWidget.include({
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            //Overide methods to user keyboard on popup
            this.keyboard_keydown_handler = function(event){
                if ($('.TextInputPopupWidget').on('keydown'))
                {

                }
                if (event.keyCode != 8 && event.keyCode != 110 && event.keyCode != 46) { // Backspace and dots
                    if (event.keyCode < 48 || (event.keyCode > 57 && event.keyCode < 96) || event.keyCode > 105){ // keyboard and numbpad numbers
                        event.preventDefault();
                        self.keyboard_handler(event);
                    }
                }
            };
            this.keyboard_handler = function(event){
                var key = '';
    
                if (event.type === "keypress") {
                    if (event.keyCode === 13) { // Enter
                        self.validate_order();
                    } else if ( event.keyCode === 190 || // Dot
                                event.keyCode === 110 ||  // Decimal point (numpad)
                                event.keyCode === 188 ||  // Comma
                                event.keyCode === 46 ) {  // Numpad dot
                        key = self.decimal_point;
                    } else if (event.keyCode >= 48 && event.keyCode <57) { // Numbers
                        key = '' + (event.keyCode - 48);
                    } else if (event.keyCode === 45) { // Minus
                        key = '-';
                    } else if (event.keyCode === 43) { // Plus
                        key = '+';
                    }
                } else { // keyup/keydown
                    if (event.keyCode === 46) { // Delete
                        key = 'CLEAR';
                    } else if (event.keyCode === 8) { // Backspace
                        key = 'BACKSPACE';
                    }
                }
            };
        },
        renderElement: function(){
            this._super()
            var self = this;
            this.$('.js_customer_cpf').ready(function($)
            {
                $('input[type=text][name=customer_cpf]').mask('000.000.000-00');
            });
            this.$('.js_customer_cpf').click(function(){
                self.click_set_customer_cpf();
            });
        },
        click_set_customer_cpf: function(){
            var order = this.pos.get_order();
            this.gui.show_popup('textinput',{
                'title': 'Input CPF',
                'confirm': function(value) {
                    order.set_client_cpf(value);
                }
            })
        },
    });
});
