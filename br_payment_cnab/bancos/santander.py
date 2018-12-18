import logging
from ..serialize.cnab240 import Cnab_240

_logger = logging.getLogger(__name__)

try:
    from pycnab240.bancos import santander
    from pycnab240.utils import get_ted_doc_finality
except ImportError:
    _logger.error('Cannot import pycnab240 dependencies.', exc_info=True)


class Santander240(Cnab_240):

    def __init__(self, payment_order):
        self._bank = santander
        self._order = payment_order
        super(Santander240, self).__init__()

    def _get_versao_lote(self, line):
        if line.payment_mode_id.payment_type in ('01', '02'):  # DOC, TED
            return 31
        elif line.payment_mode_id.payment_type == '03':  # Titulos
            return 30
        else:  # Impostos
            return 10

    def _get_cod_convenio_santander(self):
        bank_account = self._order.src_bank_account_id
        return "{:4s}{:4s}{:12s}".format(
            str(bank_account.bank_id.bic).zfill(4),
            str(bank_account.bra_number).zfill(4),
            str(bank_account.l10n_br_convenio_pagamento).zfill(12))

    def _get_header_arq(self):
        header = super()._get_header_arq()
        header.update({
            'cedente_agencia_dv': "" if (
                header.get('cedente_agencia_dv') is False)
            else header.get('cedente_agencia_dv'),
            'codigo_convenio': self._get_cod_convenio_santander()
        })
        return header

    def _get_header_lot(self, line, num_lot, lot):
        header = super()._get_header_lot(line, num_lot, lot)
        header.update({
            'forma_lancamento': self._string_to_num(
                header.get('forma_lancamento')),
            'numero_versao_lote': self._get_versao_lote(line),
            'cedente_endereco_numero': self._string_to_num(
                header.get('cedente_endereco_numero')),
            'cedente_conta': self._string_to_num(header.get('cedente_conta')),
            'cedente_agencia': int(header.get('cedente_agencia')),
            'cedente_agencia_dv': "" if (
                header.get('cedente_agencia_dv') is False)
            else header.get('cedente_agencia_dv'),
            'codigo_convenio': self._get_cod_convenio_santander()
            })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot, nome_segmento):
        segmento = super(Santander240, self)._get_segmento(
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
            'tipo_identificacao_contribuinte': 2,  # CNPJ
            'tipo_identificacao_contribuinte_alfa': '2',  # CNPJ
            'favorecido_conta': self._string_to_num(
                segmento.get('favorecido_conta'), 0),
            'tipo_movimento': int(segmento.get('tipo_movimento')),
            'codigo_camara_compensacao': self._string_to_num(
                segmento.get('codigo_camara_compensacao')),
            'codigo_instrucao_movimento': self._string_to_num(
                segmento.get('codigo_instrucao_movimento')),
            'codigo_historico_credito': self._string_to_num(
                segmento.get('codigo_historico_credito')),
            'valor_real_pagamento': self._string_to_monetary(
                segmento.get('valor_real_pagamento')),
            'valor_abatimento': self._string_to_monetary(
                segmento.get('valor_abatimento')),
            'favorecido_agencia': self._string_to_num(
                segmento.get('favorecido_agencia'), 0),
            'favorecido_nome':
                segmento.get('favorecido_nome')[:30],
            'favorecido_endereco_rua':
                segmento.get('favorecido_endereco_rua')[:30],
            'favorecido_bairro':
                segmento.get('favorecido_bairro', '')[:15],
            'favorecido_cidade':
                segmento.get('favorecido_cidade', '')[:15],
            'nome_concessionaria':
                segmento.get('nome_concessionaria', '')[:30],
            'finalidade_ted': get_ted_doc_finality(
                'santander',
                segmento.get('finalidade_doc_ted'), '01', ignore),
            'finalidade_doc': get_ted_doc_finality(
                'santander',
                segmento.get('finalidade_doc_ted'), '02', ignore),
        })
        return segmento

    def segments_per_operation(self):
        segments = super(Santander240, self).segments_per_operation()
        segments.update({
            "41": ["SegmentoA", "SegmentoB"],
            "43": ["SegmentoA", "SegmentoB"],
            "01": ["SegmentoA", "SegmentoB"],
            "03": ["SegmentoA", "SegmentoB"],
            '30': ["SegmentoJ"],
            '31': ["SegmentoJ"],
            '11': ["SegmentoO", "SegmentoW"],
            "17": ["SegmentoN_GPS"],
            "16": ["SegmentoN_DarfNormal"],
            "18": ["SegmentoN_DarfSimples"],
            "22": ["SegmentoN_GareSP", "SegmentoW"],
        })
        return segments
