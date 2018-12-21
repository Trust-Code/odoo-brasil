odoo.define('pos_nfce.screens', function (require) {
    "use strict";
    var gui = require('point_of_sale.gui');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var _t = core._t;
    screens.PaymentScreenWidget.include({
        finalize_validation: async function () {
            var self = this;
            var order = this.pos.get_order();
            if(!order.get_client()) {
                const partner = await rpc.query({
                    model: 'pos.order',
                    method: 'create_final_costumer',
                    args: [{'user_id': this.pos.get_cashier().id}]
                });
                self.pos.load_new_partners();
                const partnerParser = self.pos.db.get_partner_by_id(parseInt(partner));
                order.finalized = false;
                order.set({client: partnerParser});
                order.finalized = true;
            }

            if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) {
                this.pos.proxy.open_cashbox();
            }
            order.initialize_validation_date();
            order.finalized = true;

            if (order.is_to_invoice()) {
                var invoiced = this.pos.push_and_invoice_order(order);
                this.invoicing = true;
                invoiced.fail(function (error) {
                    self.invoicing = false;
                    order.finalized = false;
                    if (error.code < 0) {        // XmlHttpRequest Errors
                        self.gui.show_popup('error', {
                            'title': _t('The order could not be sent'),
                            'body': _t('Check your internet connection and try again.'),
                        });
                    } else if (error.code === 200) {    // OpenERP Server Errors
                        self.gui.show_popup('error-traceback', {
                            'title': error.data.message || _t("Server Error"),
                            'body': error.data.debug || _t('The server encountered an error while receiving your order.'),
                        });
                    } else {                            // ???
                        self.gui.show_popup('error', {
                            'title': _t("Unknown Error"),
                            'body': _t("The order could not be sent to the server due to an unknown error"),
                        });
                    }
                });

                invoiced.done(function () {
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