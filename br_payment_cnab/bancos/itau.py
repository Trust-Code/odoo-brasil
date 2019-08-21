from ..serialize.cnab240 import Cnab240
import time
import logging
_logger = logging.getLogger(__name__)

try:
    from pycnab240.utils import get_tipo_de_servico
    from pycnab240.utils import get_ted_doc_finality
    from pycnab240.bancos import itau
except ImportError:
    _logger.error('Cannot import from pycnab240', exc_info=True)


class Itau240(Cnab240):
    def __init__(self, pay_order):
        self._bank = itau
        self._order = pay_order
        self._operation = None
        super(Itau240, self).__init__()

    def segments_per_operation(self):
        return {
            "41": ["SegmentoA_outros_bancos", "SegmentoB"],  # TED - outros
            "03": ["SegmentoA_outros_bancos", "SegmentoB"],  # DOC - outros
            "31": ["SegmentoJ", "SegmentoJ52"],              # Títulos
            "91": ["SegmentoO"],                             # Barcode
            "17": ["SegmentoN_GPS", "SegmentoB"],            # GPS
            "16": ["SegmentoN_DarfNormal", "SegmentoB"],     # DARF normal
            "18": ["SegmentoN_DarfSimples", "SegmentoB"],    # DARF simples
            "35": ["SegmentoN_FGTS", "SegmentoB"],           # FGTS
            "22": ["SegmentoN_GareSP", "SegmentoB"],         # ICMS
            "06": ["SegmentoA_Itau_Unibanco", "SegmentoB"],  # CC - mesmo
            "07": ["SegmentoA_outros_bancos", "SegmentoB"],  # DOC - mesmo
            "43": ["SegmentoA_outros_bancos", "SegmentoB"],  # TED - mesmo
            "01": ["SegmentoA_Itau_Unibanco", "SegmentoB"],  # CC - outros
            }

    def _hour_now(self):
        return (int(time.strftime("%H%M%S")))

    def _get_header_arq(self):
        header = super(Itau240, self)._get_header_arq()

        header.update({
            'cedente_agencia': self._string_to_num(
                header.get('cedente_agencia')),
            'cedente_agencia_dv': header.get('cedente_agencia_dv') or '',
            'cedente_conta': self._string_to_num(header.get('cedente_conta')),
            'cedente_conta_dv': '0',
            'dac': self._string_to_num(header.get('cedente_conta_dv'))
        })
        return header

    def _get_header_lot(self, line, num_lot, lot):
        info_id = line.payment_information_id
        header = super(Itau240, self)._get_header_lot(line, num_lot, lot)
        self._operation = lot
        header.update({
            'forma_lancamento': self._string_to_num(
                header.get('forma_lancamento')),
            'tipo_pagamento': int(
                get_tipo_de_servico('itau', info_id.service_type)),
            'cedente_agencia': int(header.get('cedente_agencia')),
            'cedente_conta': self._string_to_num(header.get('cedente_conta')),
            'cedente_conta_dv': '0',
            'dac': self._string_to_num(header.get('cedente_conta_dv')),
            'cedente_cep': self._string_to_num(header.get('cedente_cep')),
        })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot, nome_segmento):
        segmento = super(Itau240, self)._get_segmento(
            line, lot_sequency, num_lot, nome_segmento)
        vazio, dac = self.get_dac_agencia_e_conta(segmento)
        ignore = not self.is_doc_or_ted(
            line.payment_information_id.payment_type)
        del(segmento['codigo_camara_compensacao'])
        if line.barcode:
            segmento.update({
                'codigo_de_barras': int(line.barcode[20:]),
                'codigo_de_barras_dv': self.get_dv_digitable_line(
                    self._just_numbers(line.linha_digitavel))
            })
        segmento.update({
            'numero_parcela': int(segmento.get('numero_parcela')[:13]),
            'divida_ativa_etiqueta': int(
                segmento.get('divida_ativa_etiqueta')[:13]),
            'identificador_fgts': self._string_to_num(
                segmento.get('identificador_fgts')),
            'tipo_movimento': int(segmento.get('tipo_movimento')),
            'favorecido_endereco_rua':
                segmento.get('favorecido_endereco_rua')[:30],
            'favorecido_bairro':
                segmento.get('favorecido_bairro')[:15] if segmento.get(
                    'favorecido_bairro') else '',
            'favorecido_endereco_complemento': str(
                segmento.get('favorecido_endereco_complemento'))[:15],
            'favorecido_nome': segmento.get('favorecido_nome')[:30],
            'numero_documento_cliente': str(
                segmento.get('numero_documento_cliente')),
            'favorecido_conta': self._string_to_num(
                segmento.get('favorecido_conta'), 0),
            'favorecido_agencia': self._string_to_num(
                segmento.get('favorecido_agencia'), 0),
            'valor_real_pagamento': self._string_to_monetary(
                segmento.get('valor_real_pagamento')),
            'favorecido_banco': int(line.bank_account_id.bank_id.bic) or
                int(line.barcode[:3]),
            'finalidade_ted': get_ted_doc_finality(
                'itau', segmento.get('finalidade_doc_ted'), '01', ignore),
            'finalidade_doc': get_ted_doc_finality(
                'itau', segmento.get('finalidade_doc_ted'), '02', ignore),
            'codigo_receita_tributo': int(
                segmento.get('codigo_receita_tributo') or 0),
            'vazio_dac': vazio,
            'dac': dac
        })
        return segmento

    def get_dv_digitable_line(self, linha_digitavel):
        if len(linha_digitavel) == 47:
            return int(linha_digitavel[4])
        elif len(linha_digitavel) == 48:
            return int(linha_digitavel[3])  # confirmar info

    # NOTA 11 do manual: se houverem dois digitos no dac da agencia/conta
    # o campo 42 (inicialmente vazio) deve ser utilizado
    def get_dac_agencia_e_conta(self, segmento):
        dac_agencia = segmento.get('favorecido_agencia_dv')
        dac_conta = segmento.get('favorecido_conta_dv')
        dac_agencia = False if dac_agencia is '' else dac_agencia
        dac_conta = False if dac_conta is '' else dac_conta

        if dac_agencia and dac_conta:
            return dac_agencia, dac_conta
        if dac_agencia and not dac_conta:
            return '', dac_agencia
        if not dac_agencia and dac_conta:
            return '', dac_conta
        else:
            return '', ''

    def _sum_lot_values(self, lot):
        if self._operation not in ['16', '17', '18', '35']:
            return super(Itau240, self)._sum_lot_values(lot)

        acrescimos, total_principal, outros = 0, 0, 0
        for line in lot:
            paymt_id = line.payment_information_id
            if self._operation == '17':
                outros += line.amount_total
            total_principal += line.amount_total
            acrescimos += paymt_id.interest_value + paymt_id.fine_value
        return {
            'total': total_principal + acrescimos,
            'total_principal': total_principal,
            'acrescimos': acrescimos,
            'outros': outros or 0.00
            }

    def _get_trailer_lot(self, totais, num_lot):
        trailer = super(Itau240, self)._get_trailer_lot(totais, num_lot)
        trailer.update({
            'total_valor_principal': self._float_to_monetary(
                totais.get('total_principal', 0.00)),
            'total_valor_arrecadado': trailer.get('somatorio_valores'),
            'total_valor_acrecimos': self._float_to_monetary(
                totais.get('acrescimos', 0.00)),
            'total_outro_valor': self._float_to_monetary(
                totais.get('outros', 0.00))
        })
        return trailer

    def _get_trailer_lot_name(self):
        if self._operation not in ['16', '17', '18', '35']:
            return 'TrailerLote'
        return 'TrailerLoteTributos'
