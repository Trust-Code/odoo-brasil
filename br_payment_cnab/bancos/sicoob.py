
from ..serialize.cnab240 import Cnab_240


class Sicoob240(Cnab_240):

    def __init__(self):
        super(Cnab_240, self).__init__()

    def _prepare_header_arq(self):
        header = super()._get_header_arq()

    def _prepare_segmento(self):
        pass
