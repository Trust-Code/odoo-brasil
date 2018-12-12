import logging
from ..serialize.cnab240 import Cnab_240

_logger = logging.getLogger(__name__)

try:
    from pycnab240.bancos import bradesco
    from pycnab240.utils import get_ted_doc_finality
except ImportError:
    _logger.error('Cannot import pycnab240 dependencies.', exc_info=True)


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
        header = super(Bradesco240, self)._get_header_lot(line, num_lot, lot)
        header.update({
            'forma_lancamento': self._string_to_num(
                header.get('forma_lancamento')),
            'numero_versao_lote': self._get_versao_lote(line),
            'cedente_agencia': self._string_to_num(
                header.get('cedente_agencia')),
            'cedente_conta': self._string_to_num(
                header.get('cedente_conta')),
            'cedente_cep_complemento':
            str(header.get('cedente_cep_complemento')),
        })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot, nome_segmento):
        segmento = super(Bradesco240, self)._get_segmento(
            line, lot_sequency, num_lot, nome_segmento)
        ignore = not self.is_doc_or_ted(
            line.payment_information_id.payment_type)
        if ((nome_segmento == "SegmentoW") and
                (not line.payment_information_id.cod_recolhimento_fgts)):
            return None
        segmento.update({
            'numero_parcela': int(segmento.get('numero_parcela')[:13]),
            'divida_ativa_etiqueta': int(
                segmento.get('divida_ativa_etiqueta')[:13]),
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
            'finalidade_ted': get_ted_doc_finality(
                'bradesco',
                segmento.get('finalidade_doc_ted'), '01', ignore),
            'finalidade_doc': get_ted_doc_finality(
                'bradesco',
                segmento.get('finalidade_doc_ted'), '02', ignore),
        })
        return segmento

    def segments_per_operation(self):
        segments = super(Bradesco240, self).segments_per_operation()

        segments.update({
            "41": ["SegmentoA", "SegmentoB"],
            "43": ["SegmentoA", "SegmentoB"],
            "03": ["SegmentoA", "SegmentoB"],
            "01": ["SegmentoA", "SegmentoB"],
            "30": ["SegmentoJ"],                # Títulos
            "31": ["SegmentoJ"],                # Títulos
            "17": ["SegmentoN_GPS"],            # GPS
            "16": ["SegmentoN_DarfNormal"],     # Darf Normal
            "18": ["SegmentoN_DarfSimples"],    # Darf Simples
            "11": ["SegmentoO", "SegmentoW"],   # Barcode
            "22": ["SegmentoN_GareSP"],         # Gare SP - ICMS
        })
        return segments
