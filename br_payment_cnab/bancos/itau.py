from pycnab240.utils import get_forma_de_lancamento
from pycnab240.utils import get_tipo_de_servico
from ..serialize.cnab240 import Cnab_240
from pycnab240.bancos import itau
import time


class Itau240(Cnab_240):

    def __init__(self, pay_order):
        self._bank = itau
        self._order = pay_order
        super(Itau240, self).__init__()

    def _get_segment_dict(self, segment_code, same_bank=False):

        segments_dict = {
            "01": ["SegmentoA_Diversos_outros_bancos",
                   "SegmentoB_Diversos"],  # TED
            "02": ["SegmentoA_Diversos_outros_bancos",
                   "SegmentoB_Diversos"],  # DOC
            "03": [],  # Pag. Tributo
            "04": [],  # Trib. Cod Barras
            "05": [],  # GPS
            "06": [],  # DARF normal
            "07": [],  # DARF simples
            "08": [],  # FGTS
        }

        if segment_code in ["01", "02"] and same_bank:
            return ["SegmentoA_Diversos_Itau_Unibanco", "SegmentoB_Diversos"]
        return segments_dict[segment_code]

    def create_detail(self, operation, event, lot_sequency, num_lot):

        same_bank = True if event.bank_account_id.bank_id.id \
            == self._order.payment_mode_id.bank_account_id.bank_id.id \
            else False

        for segment in self._get_segment_dict(operation, same_bank):

            self._cnab_file.add_segment(
                segment, self._get_segmento(
                    event, lot_sequency, num_lot, same_bank))
            lot_sequency += 1
        self._cnab_file.get_active_lot().get_active_event().close_event()
        return lot_sequency

    def _hour_now(self):
        return (int(time.strftime("%H%M%S")))

    def _get_header_arq(self):
        header = super(Itau240, self)._get_header_arq()

        header.update({
            'cedente_agencia': self._string_to_num(
                header.get('cedente_agencia')),
            'cedente_conta': self._string_to_num(header.get('cedente_conta')),
            'cedente_conta_dv': '0',
            'dac': self._string_to_num(header.get('cedente_conta_dv'))
        })
        return header

    def _get_header_lot(self, line, num_lot):
        info_id = line.payment_information_id
        header = super(Itau240, self)._get_header_lot(line, num_lot)
        header.update({
            'forma_pagamento': int(
                get_forma_de_lancamento('itau', info_id.payment_type)),
            'tipo_pagamento': int(
                get_tipo_de_servico('itau', info_id.service_type)),
            'tipo_servico': int(header.get('tipo_servico')),
            'cedente_agencia': int(header.get('cedente_agencia')),
            'cedente_conta': self._string_to_num(header.get('cedente_conta')),
            'cedente_conta_dv': '0',
            'dac': self._string_to_num(header.get('cedente_conta_dv')),
            'cedente_endereco_numero': self._string_to_num(
                header.get('cedente_endereco_numero')),
            'cedente_cep': self._string_to_num(header.get('cedente_cep')),
        })
        return header

    def _get_segmento(self, line, lot_sequency, num_lot, same_bank=False):
        segmento = super(Itau240, self)._get_segmento(
            line, lot_sequency, num_lot)

        # Valor do DAC é int quando é mesmo banco e str quando é outro banco...
        # NICE!
        dac = segmento.get('favorecido_conta_dv')

        if same_bank:
            dac = int(dac)

        segmento.update({
            'tipo_movimento': int(segmento.get('tipo_movimento')),
            'favorecido_cep': self._string_to_num(str(
                segmento.get('favorecido_cep')), 0),
            # 'valor_documento': self._string_to_monetary(
            #     segmento.get('valor_documento')),
            # 'valor_abatimento': self._string_to_monetary(
            #     segmento.get('valor_abatimento')),
            # 'valor_desconto': self._string_to_monetary(
            #     segmento.get('valor_desconto')),
            # 'valor_mora': self._string_to_monetary(
            #     segmento.get('valor_mora')),
            # 'valor_multa': self._string_to_monetary(
            #     segmento.get('valor_multa')),
            # 'valor_nominal_titulo': self._string_to_monetary(
            #     segmento.get('valor_nominal_titulo')),
            # 'valor_desconto_abatimento': self._string_to_monetary(
            #     segmento.get('valor_desconto_abatimento')),
            # 'valor_multa_juros': self._string_to_monetary(
            #     segmento.get('valor_multa_juros')),
            'data_vencimento': int(segmento.get('data_vencimento')),
            'favorecido_endereco_numero': self._string_to_num(
                segmento.get('favorecido_endereco_numero'), default=0),
            'favorecido_endereco_rua':
                segmento.get('favorecido_endereco_rua')[:30],
            'favorecido_endereco_complemento': str(
                segmento.get('favorecido_endereco_complemento'))[:15],
            'favorecido_inscricao_numero': self._string_to_num(
                segmento.get('favorecido_inscricao_numero')),
            'data_real_pagamento': int(segmento.get(
                'data_real_pagamento')),
            'valor_pagamento': self._string_to_monetary(
                segmento.get('valor_pagamento')),
            'data_pagamento': int(segmento.get('data_pagamento')),
            'numero_documento_cliente': str(
                segmento.get('numero_documento_cliente')),
            'favorecido_conta': self._string_to_num(
                segmento.get('favorecido_conta'), 0),
            'dac': dac,
            'favorecido_agencia': self._string_to_num(
                segmento.get('favorecido_agencia'), 0),
            'valor_real_pagamento': self._string_to_monetary(
                segmento.get('valor_real_pagamento')),
            'codigo_camara_compensacao': self._string_to_num(
                segmento.get('codigo_camara_compensacao'), default=0),
            'favorecido_banco': int(line.bank_account_id.bank_id.bic),
        })
        return segmento

    def _get_trailer_lot(self, total, num_lot):
        trailer = super(Itau240, self)._get_trailer_lot(total, num_lot)
        trailer.update({
            'quantidade_registros':
            self._cnab_file.get_total_records() + 1,
        })
        return trailer

    def _get_trailer_arq(self):
        trailer = super(Itau240, self)._get_trailer_arq()
        trailer.update({
            'totais_quantidade_registros':
            self._cnab_file.get_total_records() + 3,
        })
        return trailer
