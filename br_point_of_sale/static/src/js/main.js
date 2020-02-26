odoo.define('br_point_of_sale', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var _super_order = models.PosModel.prototype;
    var rpc = require('web.rpc');
    var session = require('web.session');

    let search_nfce = (pos_order_ids, fields) => {
        return rpc.query({
            model: 'invoice.eletronic',
            method: 'search_read',
            fields: fields,
            domain: [['pos_order_id', 'in', pos_order_ids]]
        })
    }

    models.PosModel = models.PosModel.extend({
        _save_to_server: function (order, opts) {
            var self = this
            return _super_order._save_to_server.apply(this, arguments).done((result) => self.get_nfce(result));
        },
        get_nfce: function (pos_order_ids) {
            if (!pos_order_ids.length) {
                return;
            }
            let self = this;
            self.cronSendNfe()
            .then(function() {
                self.checkNfe(self, pos_order_ids);
            });
        },
        checkNfe: function(self, pos_order_ids)
        {
            let inv_fields = ['state', 'pos_order_id', 'codigo_retorno', 'mensagem_retorno', 'id'];
            search_nfce(pos_order_ids, inv_fields).then(function (einvoices) {
                let einvoice = einvoices[0];
                if (einvoice.state == 'done') {
                    self.print_nfce(einvoice.id);
                } else if (['error', 'cancel'].indexOf(einvoice.state) > -1) {
                    alert('NFC-e Rejeitada: ' + einvoice.codigo_retorno + ' - ' + einvoice.mensagem_retorno);
                }
            });
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
