odoo.define('br_pos_base.screens', function(require){
    "use strict";

    let ajax = require('web.ajax');
    let clientScreen = require('point_of_sale.screens');

    let ClientListScreenWidget = clientScreen.ClientListScreenWidget.include({
        display_client_details: function(visibility, partner, clickpos){
            var self = this;
            let result = this._super(visibility, partner, clickpos);

            var contents = this.$('.client-details-contents');

            contents.off('click','.button.searchzip');
            contents.on('click','.button.searchzip',function(){ self.search_zip_code(partner); });
            return result;
        },
        search_zip_code: function(partner) {
            var self = this;
            var inputZip = this.$('input[name="zip"]');

            ajax.jsonRpc('/contact/zip_search', 'call', {
                  zip: inputZip.val(),
              }).then(function(result){
                  if(result.sucesso){
                      let zipcode = inputZip.val();
                      self.$('input[name="zip"]').val(zipcode.slice(0, 5) + '-' + zipcode.slice(5, 8));
                      self.$('input[name="street"]').val(result.street);
                      self.$('input[name="district"]').val(result.district);
                      self.$('select[name="city_id"]').val(result.city_id);
                      self.$('select[name="state_id"]').val(result.state_id);
                      self.$('select[name="country_id"]').val(result.country_id);
                  }else {
                      alert('Nenhum CEP encontrado!');
                  }
              }, function(err,ev){
                  alert('Erro ao pesquisar CEP');
              });
        },
    });

    return ClientListScreenWidget;
});
