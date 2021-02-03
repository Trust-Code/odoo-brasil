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
            this._super();
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
            var self = this;
            var order = this.pos.get_order();
            this.gui.show_popup('textinput',{
                'title': 'Input CPF',
                'confirm': function(value) {
                    order.set_client_cpf(value);
                    self.render_cpf_button(value);
                }
            })
        },
        render_cpf_button: function(value) {
            if(value.length > 0) {
                this.$('.js_customer_cpf').addClass("highlight");
                this.$('.js_customer_cpf').html(`<i class='fa fa-user'></i> CPF: &nbsp; ${value}`);
            } else {
                this.$('.js_customer_cpf').removeClass("highlight");
                this.$('.js_customer_cpf').html(`<i class='fa fa-user'></i> CPF na Nota?`);
            }
        },
        finalize_validation: function() {
            var self = this;
            var order = this.pos.get_order();
            order.initialize_validation_date();
            this.pos.create_invoice_eletronic(order)
            .done( () => self.finalize_pos_order())
            .fail( reason => {
                if(typeof(reason) == "object" && "data" in reason) {
                    if(reason.data.type == "xhrtimeout") {
                        alert("Não foi possível conectar ao servidor!");
                    } else {
                        alert("Erro ao realizar emissão da NFCe!");
                    }
                } else {
                    alert(reason);
                }
            })
        },
        finalize_pos_order: function() {
            var self = this;
            var order = this.pos.get_order();
            if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) { 
    
                    this.pos.proxy.open_cashbox();
            }
            order.initialize_validation_date();
            order.finalized = true;
    
            if (order.is_to_invoice()) {
                var invoiced = this.pos.push_and_invoice_order(order);
                this.invoicing = true;
    
                invoiced.fail(this._handleFailedPushForInvoice.bind(this, order, false));
    
                invoiced.done(function(){
                    self.invoicing = false;
                    self.gui.show_screen('receipt');
                });
            } else {
                this.pos.push_order(order);
                this.gui.show_screen('receipt');
            }
        }
    });
});
