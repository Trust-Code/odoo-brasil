import logging
from ..serialize.cnab240 import Cnab_240

_logger = logging.getLogger(__name__)

try:
    from pycnab240.utils import get_forma_de_lancamento
    from pycnab240.bancos import santander
except ImportError:
    _logger.debug('Cannot import pycnab240 dependencies.')


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
            str(bank_account.codigo_convenio).zfill(12))

    def _get_header_arq(self):
        header = super()._get_header_arq()
        header.update({
            'cedente_agencia_dv': "" if (
                header.get('cedente_agencia_dv') is False)
            else header.get('cedente_agencia_dv'),
            'codigo_convenio': self._get_cod_convenio_santander()
        })
        return header

    def _get_header_lot(self, line, num_lot):
        info_id = line.payment_information_id
        header = super()._get_header_lot(line, num_lot)
        header.update({
            'numero_versao_lote': self._get_versao_lote(line),
            'forma_lancamento': int(get_forma_de_lancamento(
                'santander', info_id.payment_type)),
            'cedente_cep': self._string_to_num(header.get('cedente_cep')[:6]),
            'cedente_cep_complemento': self._string_to_num(
                header.get('cedente_cep_complemento')[6:]),
            'cedente_endereco_numero': self._string_to_num(
                header.get('cedente_endereco_numero')),
            'cedente_conta': self._string_to_num(header.get('cedente_conta')),
            'cedente_agencia': int(header.get('cedente_agencia')),
            'tipo_servico': int(header.get('tipo_servico')),
            'cedente_agencia_dv': "" if (
                header.get('cedente_agencia_dv') is False)
            else header.get('cedente_agencia_dv'),
            'codigo_convenio': self._get_cod_convenio_santander()
            })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot):
        segmento = super(Santander240, self)._get_segmento(
            line, lot_sequency, num_lot)
        segmento.update({
            'tipo_identificacao_contribuinte': 2,  # CNPJ
            'tipo_identificacao_contribuinte_alfa': '2',  # CNPJ
            'favorecido_conta': self._string_to_num(
                segmento.get('favorecido_conta'), 0),
            'tipo_movimento': int(segmento.get('tipo_movimento')),
            'valor_pagamento': self._string_to_monetary(
                segmento.get('valor_pagamento')),
            'codigo_camara_compensacao': self._string_to_num(
                segmento.get('codigo_camara_compensacao')),
            'codigo_instrucao_movimento': self._string_to_num(
                segmento.get('codigo_instrucao_movimento')),
            'codigo_historico_credito': self._string_to_num(
                segmento.get('codigo_historico_credito')),
            'data_real_pagamento': self._string_to_num(
                segmento.get('data_real_pagamento')[0:10]),
            'data_vencimento': self._string_to_num(
                segmento.get('data_vencimento')),
            'data_pagamento': self._string_to_num(
                segmento.get('data_pagamento')),
            'valor_real_pagamento': self._string_to_monetary(
                segmento.get('valor_real_pagamento')),
            'valor_documento': self._string_to_monetary(
                segmento.get('valor_documento')),
            'valor_multa': self._string_to_monetary(
                segmento.get('valor_multa')),
            'valor_abatimento': self._string_to_monetary(
                segmento.get('valor_abatimento')),
            'valor_desconto': self._string_to_monetary(
                segmento.get('valor_desconto')),
            'valor_mora': self._string_to_monetary(
                segmento.get('valor_mora')),
            'favorecido_conta_dv': self._string_to_num(
                segmento.get('favorecido_conta_dv'), 0),
            'favorecido_agencia': self._string_to_num(
                segmento.get('favorecido_agencia'), 0),
            'favorecido_inscricao_numero': self._string_to_num(
                segmento.get('favorecido_inscricao_numero')),
            'favorecido_cep': self._string_to_num(str(
                segmento.get('favorecido_cep')), 0),
            'favorecido_endereco_numero': self._string_to_num(
                segmento.get('favorecido_endereco_numero'), default=0),
            'favorecido_nome':
                segmento.get('favorecido_nome')[:30],
            'favorecido_endereco_rua':
                segmento.get('favorecido_endereco_rua')[:30],
            'favorecido_bairro':
                segmento.get('favorecido_bairro', '')[:15],
            'favorecido_cidade':
                segmento.get('favorecido_cidade', '')[:15],
        })
        return segmento

    def _get_trailer_arq(self):
        trailer = super(Santander240, self)._get_trailer_arq()
        return trailer

    def _get_trailer_lot(self, total, num_lot):
        trailer = super(Santander240, self)._get_trailer_lot(total, num_lot)
        return trailer

    def segments_per_operation(self):
        segments = super(Santander240, self).segments_per_operation()
        segments.update({
            "03": ["SegmentoJ"],
            "04": ["SegmentoO"],
            "05": ["SegmentoN_GPS"],
            "06": ["SegmentoN_DarfNormal"],
            "07": ["SegmentoN_DarfSimples"],
            "08": ["SegmentoO", "SegmentoW"],
            "09": ["SegmentoN_GareSP"],
        })
        return segments
