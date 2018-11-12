import logging
from ..serialize.cnab240 import Cnab_240

_logger = logging.getLogger(__name__)

try:
    from pycnab240.utils import get_forma_de_lancamento
    from pycnab240.bancos import sicoob
except ImportError:
    _logger.debug('Cannot import pycnab240 dependencies.')


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
            'codigo_convenio': self._string_to_num(str(
                header.get('codigo_convenio'))[:20]),
            'cedente_conta': self._string_to_num(header.get('cedente_conta'))
        })
        return header

    def _get_header_lot(self, line, num_lot):
        info_id = line.payment_information_id
        header = super(Sicoob240, self)._get_header_lot(line, num_lot)
        header.update({
            'forma_lancamento':
            get_forma_de_lancamento('sicoob', info_id.payment_type),
            'tipo_servico': int(header.get('tipo_servico')),
            'cedente_agencia': int(header.get('cedente_agencia')),
            'cedente_conta_dv': self._string_to_num(
                header.get('cedente_conta_dv')),
            'cedente_conta': self._string_to_num(header.get('cedente_conta')),
            'cedente_endereco_numero': self._string_to_num(
                header.get('cedente_endereco_numero')),
            'cedente_cep': self._string_to_num(header.get('cedente_cep')[:6]),
            'cedente_cep_complemento': self._string_to_num(
                header.get('cedente_cep_complemento')[6:]),
            'codigo_convenio': self._string_to_num(str(
                header.get('codigo_convenio'))[:20]),
        })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot):
        segmento = super(Sicoob240, self)._get_segmento(
            line, lot_sequency, num_lot)
        segmento.update({
            'tipo_movimento': int(segmento.get('tipo_movimento')),
            'favorecido_cep': self._string_to_num(str(
                segmento.get('favorecido_cep')), 0),
            'favorecido_nome': segmento.get('favorecido_nome')[:30],
            'valor_documento': self._string_to_monetary(
                segmento.get('valor_documento')),
            'valor_abatimento': self._string_to_monetary(
                segmento.get('valor_abatimento')),
            'valor_desconto': self._string_to_monetary(
                segmento.get('valor_desconto')),
            'valor_mora': self._string_to_monetary(
                segmento.get('valor_mora')),
            'valor_multa': self._string_to_monetary(
                segmento.get('valor_multa')),
            'valor_nominal_titulo': self._string_to_monetary(
                segmento.get('valor_nominal_titulo')),
            'valor_desconto_abatimento': self._string_to_monetary(
                segmento.get('valor_desconto_abatimento')),
            'valor_multa_juros': self._string_to_monetary(
                segmento.get('valor_multa_juros')),
            'data_vencimento': self._string_to_num(
                segmento.get('data_vencimento')),
            'favorecido_endereco_numero': self._string_to_num(
                segmento.get('favorecido_endereco_numero'), default=0),
            'favorecido_endereco_rua':
                segmento.get('favorecido_endereco_rua')[:30],
            'favorecido_endereco_complemento': str(
                segmento.get('favorecido_endereco_complemento'))[:15],
            'favorecido_inscricao_numero': self._string_to_num(
                segmento.get('favorecido_inscricao_numero')),
            'data_real_pagamento': self._string_to_num(
                segmento.get('data_real_pagamento')[0:10]),
            'valor_pagamento': self._string_to_monetary(
                segmento.get('valor_pagamento')),
            'data_pagamento': self._string_to_num(
                segmento.get('data_pagamento')),
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
        })
        return segmento

    def _get_trailer_lot(self, total, num_lot):
        trailer = super(Sicoob240, self)._get_trailer_lot(total, num_lot)
        trailer.update({
        })
        return trailer

    def _get_trailer_arq(self):
        trailer = super(Sicoob240, self)._get_trailer_arq()
        trailer.update({
        })
        return trailer

    def segments_per_operation(self):
        segments = super(Sicoob240, self).segments_per_operation()
        segments.update({
            '03': ["SegmentoJ"],
            '04': ["SegmentoO"],
            '05': ["SegmentoN_GPS"],
            '06': ["SegmentoN_DarfNormal", "SegmentoW"],
            '07': ["SegmentoN_DarfSimples", "SegmentoW"],
        })
        return segments
