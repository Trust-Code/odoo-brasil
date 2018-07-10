
from ..serialize.cnab240 import Cnab_240


class Santander240(Cnab_240):

    def __init__(self):
        super(Cnab_240, self).__init__()

    def _prepare_header_arq(self):
        pass

    def _prepare_segmento(self):
        pass
