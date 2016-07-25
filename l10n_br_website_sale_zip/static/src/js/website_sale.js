$(document).ready(function() {

    $('#btn_search_zip').click(function(){
        var vals = {  zip: $('input[name="zip"]').val() };
        openerp.jsonRpc("/shop/zip_search", 'call', vals)
            .then(function(data) {
                if(data.sucesso){
                    $('input[name="district"]').val(data.district);
                    $('input[name="street"]').val(data.street);
                    $('select[name="country_id"]').val(data.country_id);
                    $('select[name="country_id"]').change();
                    $('select[name="state_id"]').val(data.state_id);
                    $('#input_l10n_br_city_id').val(data.city_id);
                    $('select[name="state_id"]').change();
                }else{
                    alert('Nenhum cep encontrado');
                }
            }
        );
    });
    $('#btn_search_zip_shipping').click(function(){
        var vals = {  zip: $('input[name="shipping_zip"]').val() };
        openerp.jsonRpc("/shop/zip_search", 'call', vals)
            .then(function(data) {
                if(data.sucesso){
                    $('input[name="shipping_district"]').val(data.district);
                    $('input[name="shipping_street"]').val(data.street);
                    $('select[name="shipping_country_id"]').val(data.country_id);
                    $('select[name="shipping_country_id"]').change();
                    $('select[name="shipping_state_id"]').val(data.state_id);
                    $('#input_shipping_l10n_br_city_id').val(data.city_id);
                    $('select[name="shipping_state_id"]').change();
                }else{
                    alert('Nenhum cep encontrado');
                }
            }
        );
    });
});
