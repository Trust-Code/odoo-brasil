import logging
from ..serialize.cnab240 import Cnab_240

_logger = logging.getLogger(__name__)

try:
    from pycnab240.bancos import sicoob
    from pycnab240.utils import get_ted_doc_finality
except ImportError:
    _logger.error('Cannot import pycnab240 dependencies.', exc_info=True)


class Sicoob240(Cnab_240):

    def __init__(self, pay_order):
        self._bank = sicoob
        self._order = pay_order
        super(Sicoob240, self).__init__()

    def _get_header_arq(self):
        header = super(Sicoob240, self)._get_header_arq()
        header.update({
            'cedente_conta_dv': self._string_to_num(
                header.get('cedente_conta_dv')),
            'codigo_convenio': self._string_to_num(
                self._order.src_bank_account_id.l10n_br_convenio_pagamento),
            'cedente_conta': self._string_to_num(header.get('cedente_conta'))
        })
        return header

    def _get_header_lot(self, line, num_lot, lot):
        header = super(Sicoob240, self)._get_header_lot(line, num_lot, lot)
        header.update({
            'tipo_servico': int(header.get('tipo_servico')),
            'cedente_agencia': int(header.get('cedente_agencia')),
            'cedente_conta_dv': self._string_to_num(
                header.get('cedente_conta_dv')),
            'cedente_conta': self._string_to_num(header.get('cedente_conta')),
            'codigo_convenio': self._string_to_num(
                self._order.src_bank_account_id.l10n_br_convenio_pagamento),
        })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot, nome_segmento):
        segmento = super(Sicoob240, self)._get_segmento(
            line, lot_sequency, num_lot, nome_segmento)
        ignore = not self.is_doc_or_ted(
            line.payment_information_id.payment_type)
        if (line.payment_information_id.payment_type == "08"):
            segmento.update({'nome_concessionaria': ''})
        segmento.update({
            'tipo_movimento': int(segmento.get('tipo_movimento')),
            'favorecido_nome': segmento.get('favorecido_nome')[:30],
            'valor_abatimento': self._string_to_monetary(
                segmento.get('valor_abatimento')),
            'valor_nominal_titulo': self._string_to_monetary(
                segmento.get('valor_nominal_titulo')),
            'favorecido_endereco_rua':
                segmento.get('favorecido_endereco_rua')[:30],
            'favorecido_endereco_complemento': str(
                segmento.get('favorecido_endereco_complemento'))[:15],
            'favorecido_doc_numero': self._string_to_num(
                segmento.get('favorecido_doc_numero')),
            'favorecido_conta_dv': self._string_to_num(
                segmento.get('favorecido_conta_dv'), 0),
            'favorecido_conta': self._string_to_num(
                segmento.get('favorecido_conta'), 0),
            'favorecido_agencia': self._string_to_num(
                segmento.get('favorecido_agencia'), 0),
            'valor_real_pagamento': self._string_to_monetary(
                segmento.get('valor_real_pagamento')),
            'codigo_instrucao_movimento': self._string_to_num(
                segmento.get('codigo_instrucao_movimento')),
            'codigo_camara_compensacao': self._string_to_num(
                segmento.get('codigo_camara_compensacao')),
            'finalidade_ted': get_ted_doc_finality(
                'sicoob', segmento.get('finalidade_doc_ted'), '01', ignore),
            'finalidade_doc': get_ted_doc_finality(
                'sicoob', segmento.get('finalidade_doc_ted'), '02', ignore),
            'nome_concessionaria': (
                '' if line.payment_information_id.payment_type == '10'
                else segmento.get('nome_concessionaria'))
        })
        return segmento

    def segments_per_operation(self):
        segments = super(Sicoob240, self).segments_per_operation()
        segments.update({
            "01": ["SegmentoA", "SegmentoB"],
            "03": ["SegmentoA", "SegmentoB"],
            "41": ["SegmentoA", "SegmentoB"],
            "43": ["SegmentoA", "SegmentoB"],
            '30': ["SegmentoJ"],
            '31': ["SegmentoJ"],
            '11': ["SegmentoO"],
            '17': ["SegmentoN_GPS"],
            '16': ["SegmentoN_DarfNormal", "SegmentoW"],
            '18': ["SegmentoN_DarfSimples", "SegmentoW"],
        })
        return segments
