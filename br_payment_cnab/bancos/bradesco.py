import logging
from ..serialize.cnab240 import Cnab_240

_logger = logging.getLogger(__name__)


class Bradesco240(Cnab_240):

    def __init__(self):
        super(Cnab_240, self).__init__()

    def _prepare_header_arq(self):
        pass

    def _prepare_header_lot(self, line, lot):
        segment = super()._get_header_lot(line)
        segment.update({
            'numero_versao_lote': 31,
        })
