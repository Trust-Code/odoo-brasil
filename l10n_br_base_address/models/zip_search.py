import re
import logging
from odoo import models

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
except ImportError:
    _logger.error("Cannot import zeep library", exc_info=True)


class ZipSearchMixin(models.AbstractModel):
    _name = 'zip.search.mixin'
    _description = 'Pesquisa de CEP'

    def search_address_by_zip(self, zip_code):
        zip_code = re.sub('[^0-9]', '', zip_code or '')
        client = Client('https://apps.correios.com.br/SigepMasterJPA/AtendeClienteService/AtendeCliente?wsdl') # noqa
        try:
            res = client.service.consultaCEP(zip_code)
        except:
            return {}
        state = self.env['res.country.state'].search(
            [('country_id.code', '=', 'BR'),
             ('code', '=', res['uf'])])

        city = self.env['res.city'].search([
            ('name', '=ilike', res['cidade']),
            ('state_id', '=', state.id)])
        
        if(res['end'] == None):
            res['end'] = False
        if(res['bairro'] == None):
            res['bairro'] = False
        
        return {
            'zip': zip_code,
            'street': res['end'],
            'l10n_br_district': res['bairro'],
            'country_id': state.country_id.id,
            'state_id': state.id,
            'city_id': city.id
        }
