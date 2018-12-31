# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
import logging
from io import StringIO
from decimal import Decimal
from datetime import datetime, date

_logger = logging.getLogger(__name__)

try:
    from pycnab240.file import File
    from pycnab240.utils import get_operation
except ImportError:
    _logger.error('Cannot import pycnab240', exc_info=True)


class Cnab_240(object):

    def _hour_now(self):
        return (int(datetime.now().strftime("%H%M%S")[0:4]))

    def _string_to_monetary(self, numero, precision=2):
        frmt = '{:.%df}' % precision
        return Decimal(frmt.format(numero))

    def _float_to_monetary(self, number, precision=2):
        return Decimal(str(number)).quantize(Decimal('0.01'))

    def _just_numbers(self, value):
        return re.sub('[^0-9]', '', str(value or ''))

    def _string_to_num(self, toTransform, default=None):
        if not toTransform:
            return default or 0
        value = re.sub('[^0-9]', '', str(toTransform))
        if not value:
            return default or 0
        try:
            return int(value)
        except ValueError:
            if default is not None:
                return default
            else:
                raise

    def format_date(self, date_value):
        if not date_value:
            return ''
        if not isinstance(date_value, (date, datetime)):
            date_value = datetime.strptime(date_value[0:10], "%Y-%m-%d")
        return date_value.strftime("%d%m%Y")

    def is_doc_or_ted(self, op):
        if op == '01' or op == '02':
            return True
        return False

    def _get_header_arq(self):
        bank = self._order.src_bank_account_id
        headerArq = {
            'cedente_inscricao_tipo': 2,  # 0 = Isento, 1 = CPF, 2 = CNPJ
            # número do registro da empresa
            'cedente_inscricao_numero': self._string_to_num(
                self._order.company_id.cnpj_cpf),
            # Usado pelo Banco para identificar o contrato - númerodo banco(4),
            # códigode agência(4 "sem DV"), número do convênio(12).
            'codigo_convenio': bank.l10n_br_convenio_pagamento,
            'cedente_agencia': self._string_to_num(bank.bra_number, 0),
            'cedente_agencia_dv': bank.bra_number_dig,
            'cedente_conta': self._string_to_num(bank.acc_number),
            'cedente_conta_dv': bank.acc_number_dig,
            'cedente_nome': self._order.company_id.legal_name[:30],
            'data_geracao_arquivo': int(self.format_date(date.today())),
            'hora_geracao_arquivo': self._hour_now(),
            'numero_sequencial_arquivo': self._order.file_number,
        }
        return headerArq

    def _get_segmento(self, line, lot_sequency, num_lot, nome_segmento):
        information_id = line.payment_information_id
        segmento = {
            'numero_parcela': str(information_id.numero_parcela_icms),
            'divida_ativa_etiqueta': str(information_id.divida_ativa_etiqueta),
            "cedente_inscricao_numero": self._string_to_num(
                self._order.company_id.cnpj_cpf),
            "identificador_fgts": information_id.identificacao_fgts,
            "lacre_conectividade_social": information_id.conec_social_fgts,
            "lacre_conectividade_social_dv":
                information_id.conec_social_dv_fgts,
            "controle_lote": num_lot,
            "sequencial_registro_lote": lot_sequency,
            "tipo_movimento": information_id.mov_type,
            "codigo_instrucao_movimento": information_id.mov_instruc,
            "codigo_camara_compensacao": information_id.operation_code,
            # adicionar campo para o banco do clinte com um valor default
            "favorecido_codigo_banco": line.bank_account_id.bank_id.name,
            "favorecido_banco": int(line.bank_account_id.bank_id.bic),
            "favorecido_agencia": line.bank_account_id.bra_number,
            "favorecido_agencia_dv": line.bank_account_id.bra_number_dig or '',
            "favorecido_conta": line.bank_account_id.acc_number,
            "favorecido_conta_dv": line.bank_account_id.acc_number_dig or '',
            "favorecido_agencia_conta_dv": '',
            "favorecido_nome":
            line.partner_id.legal_name or line.partner_id.name,
            "favorecido_doc_numero": line.partner_id.cnpj_cpf,
            "numero_documento_cliente": line.nosso_numero,
            "data_pagamento": int(self.format_date(line.date_maturity)),
            "valor_pagamento": self._float_to_monetary(line.amount_total),
            "data_real_pagamento": int(self.format_date(
                self._order.data_emissao_cnab)),
            "valor_real_pagamento": self._float_to_monetary(line.value_final),
            "mensagem2": information_id.message2 or '',
            "finalidade_doc_ted": information_id.mov_finality or '',
            "favorecido_emissao_aviso_alfa": information_id.warning_code,
            "favorecido_emissao_aviso": int(information_id.warning_code),
            "favorecido_inscricao_tipo":
            2 if line.partner_id.is_company else 1,
            "favorecido_inscricao_numero": self._string_to_num(
                line.partner_id.cnpj_cpf),
            "favorecido_endereco_rua": line.partner_id.street or '',
            "favorecido_endereco_numero": self._string_to_num(
                line.partner_id.number, default=0),
            "favorecido_endereco_complemento": line.partner_id.street2 or '',
            "favorecido_bairro": line.partner_id.district or '',
            "favorecido_cidade": line.partner_id.city_id.name or '',
            "favorecido_cep": self._string_to_num(line.partner_id.zip),
            "cep_complemento": self._just_numbers(line.partner_id.zip[5:]),
            "favorecido_uf": line.partner_id.state_id.code or '',
            "valor_documento": self._float_to_monetary(line.amount_total),
            "valor_abatimento": self._float_to_monetary(
                information_id.rebate_value),
            "valor_desconto": self._float_to_monetary(
                information_id.discount_value),
            "valor_mora": self._float_to_monetary(
                information_id.interest_value),
            "valor_multa": self._float_to_monetary(information_id.fine_value),
            "hora_envio_ted": self._hour_now(),
            "codigo_historico_credito": information_id.credit_hist_code,
            "cedente_nome": self._order.company_id.legal_name[:30],
            "valor_nominal_titulo":  self._float_to_monetary(
                line.amount_total),
            "valor_desconto_abatimento": self._float_to_monetary(
                information_id.rebate_value + information_id.discount_value),
            "valor_multa_juros": self._float_to_monetary(
                information_id.interest_value + information_id.fine_value),
            "codigo_moeda": int(information_id.currency_code),
            "codigo_de_barras": self._string_to_num(line.barcode),
            "codigo_de_barras_alfa": line.barcode or '',
            # TODO Esse campo deve ser obtido a partir do payment_mode_id
            "nome_concessionaria":
            (line.partner_id.legal_name or line.partner_id.name)[:30],
            "data_vencimento": int(self.format_date(line.date_maturity)),
            "valor_juros_encargos": self._string_to_monetary(
                information_id.interest_value),
            # GPS
            "contribuinte_nome": self._order.company_id.legal_name[:30],
            "codigo_receita_tributo": information_id.codigo_receita or '',
            "tipo_identificacao_contribuinte": 1,
            "identificacao_contribuinte": self._string_to_num(
                self._order.company_id.cnpj_cpf),
            "identificacao_contribuinte_alfa": self._just_numbers(
                self._order.company_id.cnpj_cpf),
            "codigo_identificacao_tributo": information_id.tax_identification\
                or '',
            "mes_ano_competencia": self.get_mes_ano_competencia(line),
            "valor_previsto_inss": self._string_to_monetary(line.amount_total),
            # DARF
            "periodo_apuracao": int(self.format_date(line.invoice_date) or 0),
            "valor_principal": self._string_to_monetary(line.amount_total),
            "valor_receita_bruta_acumulada": self._string_to_monetary(
                self._order.company_id.annual_revenue),
            "percentual_receita_bruta_acumulada": self._string_to_monetary(
                information_id.percentual_receita_bruta_acumulada),
            # GARE SP
            'inscricao_estadual': int(self._string_to_num(
                self._order.company_id.inscr_est)),
            'valor_receita': self._string_to_monetary(line.amount_total),
            'numero_referencia': self._string_to_num(
                information_id.numero_referencia),
        }
        return segmento

    def _get_trailer_arq(self):
        trailerArq = {
        }
        return trailerArq

    def _get_trailer_lot(self, totais, num_lot):
        trailer_lot = {
            "controle_lote": num_lot,
            "somatorio_valores": self._string_to_monetary(
                totais.get('total'))
        }
        return trailer_lot

    def _get_header_lot(self, line, num_lot, lot):
        information_id = line.payment_information_id
        bank = self._order.src_bank_account_id
        header_lot = {
            "forma_lancamento": lot,
            "controle_lote": num_lot,
            "tipo_servico": int(information_id.service_type),
            "cedente_inscricao_tipo": 2,
            "cedente_inscricao_numero": self._string_to_num(
                self._order.company_id.cnpj_cpf),
            "codigo_convenio": str(bank.l10n_br_convenio_pagamento),
            "cedente_agencia": bank.bra_number,
            "cedente_agencia_dv": bank.bra_number_dig or '',
            "cedente_conta": bank.acc_number,
            "cedente_conta_dv": bank.acc_number_dig or '',
            "cedente_nome": self._order.company_id.legal_name[:30],
            "mensagem1": information_id.message1 or '',
            "cedente_endereco_rua": self._order.company_id.street,
            "cedente_endereco_numero": self._string_to_num(
                self._order.company_id.number),
            "cedente_endereco_complemento": str(
                self._order.company_id.street2)[0:15] if
            self._order.company_id.street2 else '',
            "cedente_cidade": str(self._order.company_id.city_id.name)[:20] if
            self._order.company_id.city_id.name else '',
            "cedente_cep": self._string_to_num(self._order.company_id.zip[:6]),
            "cedente_cep_complemento": self._string_to_num(
                self._order.company_id.zip[6:]),
            "cedente_uf": self._order.company_id.state_id.code,
        }
        return header_lot

    def get_operation(self, line):
        bank_origin = line.src_bank_account_id.bank_id.bic
        bank_dest = line.bank_account_id.bank_id.bic
        tit_origin = line.src_bank_account_id.partner_id
        tit_dest = line.bank_account_id.partner_id
        op = line.payment_information_id.payment_type
        return get_operation(bank_origin, bank_dest, tit_origin, tit_dest, op)

    def _ordenate_lines(self, listOfLines):
        operacoes = {}
        for line in listOfLines:
            op = self.get_operation(line)
            if op in operacoes:
                operacoes[op].append(line)
            else:
                operacoes[op] = [line]
        self._lot_qty = len(operacoes)
        return operacoes

    def __init__(self):
        self._cnab_file = File(self._bank)

    def create_cnab(self, listOfLines):
        self._cnab_file.add_header(self._get_header_arq())
        self.create_details(self._ordenate_lines(listOfLines))

    def create_details(self, operacoes):
        num_lot = 1
        for lote, events in operacoes.items():
            self._create_header_lote(events[0], num_lot, lote)
            lot_sequency = 1
            for event in events:
                lot_sequency = self.create_detail(
                    lote, event, lot_sequency, num_lot)
            totais_lote = self._sum_lot_values(events)
            self._create_trailer_lote(totais_lote, num_lot)
            num_lot = num_lot + 1

    def _create_header_lote(self, line, num_lot, lot):
        self._cnab_file.add_segment(
            'HeaderLote', self._get_header_lot(line, num_lot, lot))

    def create_detail(self, operation, event, lot_sequency, num_lot):
        segments = self.segments_per_operation().get(operation, [])
        if not segments:
            raise Exception(
                'Pelo menos um segmento por tipo deve ser implementado!')
        for nome_segmento in segments:
            vals = self._get_segmento(
                event, lot_sequency, num_lot, nome_segmento)
            if vals is not None:
                self._cnab_file.add_segment(nome_segmento, vals)
            lot_sequency += 1
        self._cnab_file.get_active_lot().get_active_event(None).close_event()
        return lot_sequency

    def segments_per_operation(self):
        return {
            "01": ["SegmentoA", "SegmentoB"],
            "03": ["SegmentoA", "SegmentoB"],
        }

    def _get_trailer_lot_name(self):
        return 'TrailerLote'

    def _create_trailer_lote(self, totais, num_lot):
        seg_name = self._get_trailer_lot_name()
        self._cnab_file.add_segment(
            seg_name, self._get_trailer_lot(totais, num_lot))
        self._cnab_file.get_active_lot().close_lot()

    def _generate_file(self):
        arquivo = StringIO()
        self._cnab_file.write_to_file(arquivo)
        return arquivo.getvalue()

    def write_cnab(self):
        self._cnab_file.add_trailer(self._get_trailer_arq())
        self._cnab_file.close_file()
        return self._generate_file().encode()

    def _sum_lot_values(self, lot):
        total = 0
        for line in lot:
            total = total + line.value_final
        return {'total': total}

    def get_mes_ano_competencia(self, line):
        if not line.invoice_date:
            return 0
        date = datetime.strptime(line.invoice_date, "%Y-%m-%d")
        return int('{}{}'.format(date.month, date.year))
