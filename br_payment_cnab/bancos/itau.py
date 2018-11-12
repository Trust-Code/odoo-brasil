from ..serialize.cnab240 import Cnab_240
import time
import logging
_logger = logging.getLogger(__name__)

try:
    from pycnab240.utils import get_forma_de_lancamento
    from pycnab240.utils import get_tipo_de_servico
    from pycnab240.utils import get_ted_doc_finality
    from pycnab240.bancos import itau
except ImportError:
    _logger.error('Cannot import from pycnab240', exc_info=True)


class Itau240(Cnab_240):

    def __init__(self, pay_order):
        self._bank = itau
        self._order = pay_order
        super(Itau240, self).__init__()

    def segments_per_operation(self):
        return {
            "01": ["SegmentoA_outros_bancos", "SegmentoB"],
            "02": ["SegmentoA_outros_bancos", "SegmentoB"],
            "97": ["SegmentoA_outros_bancos", "SegmentoB"],
            "98": ["SegmentoA_outros_bancos", "SegmentoB"],
            "99": ["SegmentoA_Itau_Unibanco", "SegmentoB"]
            }

    def is_same_bank(self, line):
        bank_line = line.bank_account_id.bank_id.bic
        if bank_line == '341' or bank_line == '409':
            return True
        else:
            return False

    def is_same_titularity(self, line):
        partner = line.src_bank_account_id.partner_id
        if partner == line.bank_account_id.partner_id:
            return True
        else:
            return False

    def set_position(self, operation, line, dic):
        if not dic.get(operation, False):
            dic[operation] = [line]
        else:
            dic[operation].append(line)
        return dic

    def get_operation(self, line):
        pay_type = line.payment_information_id.payment_type
        if self.is_same_bank(line):
            return '99'
        if self.is_same_titularity(line):
            if pay_type == '01':
                return '98'
            elif pay_type == '02':
                return '97'
        else:
            return pay_type

    def _ordenate_lines(self, listOfLines):
        operacoes = {}
        for line in listOfLines:
            operacoes = self.set_position(
                self.get_operation(line), line, operacoes)
        self._lot_qty = len(operacoes)
        return operacoes

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

    def _get_header_lot(self, line, num_lot):
        info_id = line.payment_information_id
        header = super(Itau240, self)._get_header_lot(line, num_lot)
        header.update({
            'forma_pagamento': int(
                get_forma_de_lancamento('itau', self.get_operation(line))),
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

    def _get_segmento(self, line, lot_sequency, num_lot):
        segmento = super(Itau240, self)._get_segmento(
            line, lot_sequency, num_lot)

        if not segmento.get('favorecido_cidade'):
            segmento.update({'favorecido_cidade': ''})  # Verificar se isso
            # deve existir mesmo. Talvez tratar o erro da cidade faltando,
            # pro caso de obrigatoriedade desse campo
        del(segmento['codigo_camara_compensacao'])
        segmento.update({
            'tipo_movimento': int(segmento.get('tipo_movimento')),
            'favorecido_cep': self._string_to_num(str(
                segmento.get('favorecido_cep')), 0),
            'data_vencimento': self._string_to_num(
                (segmento.get('data_vencimento'))),
            'favorecido_endereco_numero': self._string_to_num(
                segmento.get('favorecido_endereco_numero'), default=0),
            'favorecido_endereco_rua':
                segmento.get('favorecido_endereco_rua')[:30],
            'favorecido_bairro':
                segmento.get('favorecido_bairro')[:15] if segmento.get(
                    'favorecido_bairro') else '',
            'favorecido_endereco_complemento': str(
                segmento.get('favorecido_endereco_complemento'))[:15],
            'favorecido_inscricao_numero': self._string_to_num(
                segmento.get('favorecido_inscricao_numero')),
            'favorecido_nome': segmento.get('favorecido_nome')[:30],
            'data_real_pagamento': int(segmento.get(
                'data_real_pagamento')),
            'valor_pagamento': self._string_to_monetary(
                segmento.get('valor_pagamento')),
            'data_pagamento': self._string_to_num(
                segmento.get('data_pagamento')),
            'numero_documento_cliente': str(
                segmento.get('numero_documento_cliente')),
            'favorecido_conta': self._string_to_num(
                segmento.get('favorecido_conta'), 0),
            'favorecido_agencia': self._string_to_num(
                segmento.get('favorecido_agencia'), 0),
            'valor_real_pagamento': self._string_to_monetary(
                segmento.get('valor_real_pagamento')),
            'favorecido_banco': int(line.bank_account_id.bank_id.bic),
            'finalidade_doc_ted': get_ted_doc_finality(
                'itau', line.payment_information_id.payment_type,
                segmento.get('finalidade_doc_ted'))
        })
        return segmento

    def _get_trailer_lot(self, total, num_lot):
        trailer = super(Itau240, self)._get_trailer_lot(total, num_lot)
        trailer.update({
        })
        return trailer

    def _get_trailer_arq(self):
        trailer = super(Itau240, self)._get_trailer_arq()
        trailer.update({
        })
        return trailer
