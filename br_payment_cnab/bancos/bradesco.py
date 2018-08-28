import logging
from ..serialize.cnab240 import Cnab_240

_logger = logging.getLogger(__name__)

try:
    from pycnab240.utils import get_forma_de_lancamento
except ImportError:
    _logger.debug('Cannot import pycnab240 dependencies.')


class Bradesco240(Cnab_240):

    def __init__(self):
        super(Cnab_240, self).__init__()

    def _prepare_header_arq(self):
        pass

    def _prepare_header_lot(self, line):
        info_id = line.payment_information_id
        segment = super()._get_header_lot(line)
        segment.update({
            'numero_versao_lote': 31,
            'forma_lancamento':
            get_forma_de_lancamento('bradesco', info_id.payment_type),
        })
