from pycnab240.utils import get_forma_de_lancamento
from ..serialize.cnab240 import Cnab_240
from pycnab240.bancos import santander


class Santander240(Cnab_240):

    def __init__(self, payment_order):
        self._bank = santander
        self._order = payment_order
        super(Cnab_240, self).__init__()

    def _get_header_arq(self):
        header = super()._get_header_arq()
        return header

    def _get_header_lot(self, line, num_lot):
        info_id = line.payment_information_id
        header = super()._get_header_lot(line, num_lot)
        header.update({
            'numero_versao_lote': 31,
            'forma_lancamento':
            get_forma_de_lancamento('santander', info_id.payment_type)
            })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot):
        segment = super(Santander240, self)._get_segmento(
            line, lot_sequency, num_lot)
        return segment

    def _get_trailer_arq(self):
        trailer = super(Santander240, self)._get_trailer_arq()
        return trailer

    def _get_trailer_lot(self, total, num_lot):
        trailer = super(Santander240, self)._get_trailer_lot(total, num_lot)
        return trailer
