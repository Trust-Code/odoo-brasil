import logging
from ..serialize.cnab240 import Cnab_240

_logger = logging.getLogger(__name__)


class Bradesco240(Cnab_240):

    def __init__(self, payment_order):
        self._bank = bradesco
        self._order = payment_order
        super(Bradesco240, self).__init__()

    def _get_versao_lote(self, line):
        if line.payment_mode_id.payment_type in ('01', '02'):  # DOC, TED
            return 31
        elif line.payment_mode_id.payment_type == '03':  # Titulos
            return 30
        else:  # Impostos
            return 10

    def _get_header_arq(self):
        header = super(Bradesco240, self)._get_header_arq()
        header.update({
            'cedente_agencia': self._string_to_num(
                header.get('cedente_agencia')),
        })
        return header

    def _get_header_lot(self, line, num_lot, lot):
        info_id = line.payment_information_id
        header = super(Bradesco240, self)._get_header_lot(line, num_lot)
        header.update({
            'numero_versao_lote': self._get_versao_lote(line),
            'cedente_agencia': self._string_to_num(
                header.get('cedente_agencia')),
            'cedente_conta': self._string_to_num(
                header.get('cedente_conta')),
            'cedente_cep_complemento':
            str(header.get('cedente_cep_complemento')),
        })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot):
        segmento = super(Bradesco240, self)._get_segmento(
            line, lot_sequency, num_lot)
        segmento.update({
            'tipo_movimento': int(segmento.get('tipo_movimento')),
            'codigo_camara_compensacao': self._string_to_num(
                segmento.get('codigo_camara_compensacao')),
            'codigo_instrucao_movimento': self._string_to_num(
                segmento.get('codigo_instrucao_movimento')),
            'favorecido_conta': self._string_to_num(
                segmento.get('favorecido_conta'), 0),
            'favorecido_conta_dv': self._string_to_num(
                segmento.get('favorecido_conta_dv'), 0),
            'favorecido_agencia': self._string_to_num(
                segmento.get('favorecido_agencia'), 0),
            'favorecido_cep': self._string_to_num(
                str(segmento.get('favorecido_cep'))[:5]),
        })
        return segmento

    def segments_per_operation(self):
        segments = super(Bradesco240, self).segments_per_operation()
        segments.update({
            # CORRIGIRRRR!!
            "03": ["SegmentoJ"],
            "04": ["SegmentoO"],
            "05": ["SegmentoN_GPS"],
            "06": ["SegmentoN_DarfNormal"],
            "07": ["SegmentoN_DarfSimples"],
            "08": ["SegmentoO", "SegmentoW"],
            "09": ["SegmentoN_GareSP"],
        })
        return segments
