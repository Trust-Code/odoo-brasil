from pycnab240.utils import get_forma_de_lancamento
from ..serialize.cnab240 import Cnab_240


class Santander240(Cnab_240):

    def __init__(self):
        super(Cnab_240, self).__init__()

    def _prepare_header_arq(self):
        pass

    def _prepare_header_lot(self, line):
        info_id = line.payment_information_id
        segment = super()._get_header_lot(line)
        segment.update({
            'forma_lancamento':
            get_forma_de_lancamento('santander', info_id.payment_type),
