odoo.define('br_point_of_sale', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var models = require('point_of_sale.models');
    var _super_posorder = models.Order.prototype;

    let search_nfce = (edoc_ids, fields) => {
        return rpc.query({
            model: 'invoice.eletronic',
            method: 'search_read',
            fields: fields,
            domain: [['id', 'in', edoc_ids]]
        })
    }

    models.PosModel = models.PosModel.extend({
        create_invoice_eletronic: function(pos_order) {
            var self = this;
            var args = [0, [pos_order.export_as_JSON()]]
            return rpc.query({
                model: 'invoice.eletronic',
                method: 'create_from_ui',
                args: args,
                kwargs: {context: session.user_context},
            }, {
                timeout: 7500,
            }).then( edoc_ids => self.get_nfce(edoc_ids));
        },
        get_nfce: function (edoc_ids) {
            if (!edoc_ids.length) {
                return (new $.Deferred()).resolve();
            }
            let self = this;
            return self.cronSendNfe().then(function() {
                return self.checkNfe(self, edoc_ids);
            });
        },
        checkNfe: function(self, edoc_ids)
        {
            let inv_fields = ['state', 'pos_order_id', 'codigo_retorno', 'mensagem_retorno', 'id'];
            var def = $.Deferred();
            search_nfce(edoc_ids, inv_fields).then(function (einvoices) {
                let einvoice = einvoices[0];
                if (einvoice.state == 'done') {
                    self.print_nfce(einvoice.id);
                    def.resolve();
                } else if (['error', 'cancel'].indexOf(einvoice.state) > -1) {
                    def.reject('NFC-e Rejeitada: ' + einvoice.codigo_retorno + ' - ' + einvoice.mensagem_retorno);
                }
            });
            return def;
        },
        print_nfce: function (einvoice_id)
        {
            var self = this;
                console.log('Printing');
                let base_url = session['web.base.url'];
                let w = window.open(`${base_url}/report/pdf/br_nfe.main_template_br_nfe_danfe/${einvoice_id}`);
                if(w) {
                    w.print();
                }
                else{
                    alert('Verifique se o bloqueio de pop-ups está ativado!');
                }
        },
        cronSendNfe: function () {
            return rpc.query({
                model: 'invoice.eletronic',
                method: 'cron_send_nfe',
                args: [[]]
            })
        }
    });
    return models;
});
