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
except ImportError:
    _logger.info('Cannot import pytrustnfe', exc_info=True)


class Cnab_240(object):

    def _hour_now(self):
        return (int(datetime.now().strftime("%H%M%S")[0:4]))

    def _string_to_monetary(self, numero, precision=2):
        frmt = '{:.%df}' % precision
        return Decimal(frmt.format(numero))

    def _string_to_num(self, toTransform, default=None):
        value = re.sub('[^0-9]', '', str(toTransform))
        if not value:
            return 0
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

    def _get_header_arq(self):
        payment = self._order.payment_mode_id
        bank = payment.bank_account_id
        headerArq = {
            'cedente_inscricao_tipo': 2,  # 0 = Isento, 1 = CPF, 2 = CNPJ
            # número do registro da empresa
            'cedente_inscricao_numero': self._string_to_num(
                self._order.company_id.cnpj_cpf),
            # Usado pelo Banco para identificar o contrato - númerodo banco(4),
            # códigode agência(4 "sem DV"), número do convênio(12).
            'codigo_convenio': bank.codigo_convenio,
            # Para ordem de pagamento, saque em uma agência -número da agência,
            # caso contrário preencher com zeros.
            'cedente_agencia': self._string_to_num(bank.bra_number, 0),
            'cedente_agencia_dv': bank.bra_number_dig,
            'cedente_conta': self._string_to_num(bank.acc_number),
            'cedente_conta_dv': bank.acc_number_dig,
            'cedente_nome': self._order.company_id.name,
            'data_geracao_arquivo': int(self.format_date(date.today())),
            'hora_geracao_arquivo': self._hour_now(),
            'numero_sequencial_arquivo': self._order.file_number,
        }
        return headerArq

    def _get_segmento(self, line, lot_sequency, num_lot):
        information_id = line.payment_information_id
        segmento = {
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
            "favorecido_nome": line.partner_id.name,
            "favorecido_doc_numero": line.partner_id.cnpj_cpf,
            "numero_documento_cliente": line.nosso_numero,
            "data_pagamento": self.format_date(line.date_maturity),
            "valor_pagamento": line.value,
            "data_real_pagamento": self.format_date(
                self._order.data_emissao_cnab),
            "valor_real_pagamento": line.value_final,  # TODO
            "mensagem2": information_id.message2 or '',
            "finalidade_doc_ted": information_id.mov_finality,
            "finalidade_ted": information_id.finality_ted,
            "favorecido_emissao_aviso": int(information_id.warning_code) if
            information_id.warning_code else 0,
            "favorecido_inscricao_tipo":
            2 if line.partner_id.is_company else 1,
            "favorecido_inscricao_numero": line.partner_id.cnpj_cpf,
            "favorecido_endereco_rua": line.partner_id.street or '',
            "favorecido_endereco_numero": line.partner_id.number or '',
            "favorecido_endereco_complemento": line.partner_id.street2 or '',
            "favorecido_bairro": line.partner_id.district,
            "favorecido_cidade": line.partner_id.city_id.name,
            "favorecido_cep": line.partner_id.zip,
            "favorecido_uf": line.partner_id.state_id.code,
            "valor_documento": line.value,
            "valor_abatimento": information_id.rebate_value,
            "valor_desconto": information_id.discount_value,
            "valor_mora": information_id.mora_value,
            "valor_multa": information_id.duty_value,
            "hora_envio_ted": self._hour_now(),
            "codigo_historico_credito": information_id.credit_hist_code,
            "cedente_nome": self._order.company_id.name,
            "valor_nominal_titulo": line.value,
            "valor_desconto_abatimento": information_id.rebate_value +
                information_id.discount_value,
            "valor_multa_juros": information_id.mora_value +
                information_id.duty_value,
            "codigo_moeda": information_id.currency_code,
            "codigo_de_barras": int("0"*44),
            # TODO Esse campo deve ser obtido a partir do payment_mode_id
            "nome_concessionaria": information_id.agency_name or '',
            "data_vencimento": self.format_date(line.date_maturity),
            # GPS
            "contribuinte_nome": self._order.company_id.name,
            "valor_total_pagamento": self._string_to_monetary(
                line.value_final),
            "codigo_receita_tributo": information_id.codigo_receita or '',
            "tipo_identificacao_contribuinte": 1,
            "identificacao_contribuinte": self._string_to_num(
                self._order.company_id.cnpj_cpf),
            "codigo_identificacao_tributo": information_id.tax_identification\
                or '',
            "mes_ano_competencia": self.get_mes_ano_competencia(line),
            "valor_previsto_inss": self._string_to_monetary(line.value),
            # DARF
            "periodo_apuracao": self.format_date(line.invoice_date),
            "valor_principal": self._string_to_monetary(line.value),
        }
        return segmento

    def _get_trailer_arq(self):
        trailerArq = {
        }
        return trailerArq

    def _get_trailer_lot(self, total, num_lot):
        trailer_lot = {
            "controle_lote": num_lot,
            "somatorio_valores": self._string_to_monetary(total)
        }
        return trailer_lot

    def _get_header_lot(self, line, num_lot):
        information_id = line.payment_information_id
        payment = self._order.payment_mode_id
        bank = payment.bank_account_id
        header_lot = {
            "controle_lote": num_lot,
            "tipo_servico": information_id.service_type,
            "cedente_inscricao_tipo": 2,
            "cedente_inscricao_numero": self._string_to_num(
                payment.company_id.cnpj_cpf),
            "codigo_convenio": str(bank.codigo_convenio),
            "cedente_agencia": bank.bra_number,
            "cedente_agencia_dv": bank.bra_number_dig or '',
            "cedente_conta": bank.acc_number,
            "cedente_conta_dv": bank.acc_number_dig or '',
            "cedente_nome": payment.company_id.name,
            "mensagem1": information_id.message1 or '',
            "cedente_endereco_rua": self._order.company_id.street,
            "cedente_endereco_numero": payment.company_id.number,
            "cedente_endereco_complemento": str(
                self._order.company_id.street2)[0:15] if
            self._order.company_id.street2 else '',
            "cedente_cidade": str(self._order.company_id.city_id.name)[:20] if
            self._order.company_id.city_id.name else '',
            "cedente_cep": self._order.company_id.zip,
            "cedente_cep_complemento": self._order.company_id.zip,
            "cedente_uf": self._order.company_id.state_id.code,
        }
        return header_lot

    def _ordenate_lines(self, listOfLines):
        operacoes = {}
        for line in listOfLines:
            if line.payment_information_id.payment_type in operacoes:
                operacoes[
                    line.payment_information_id.payment_type].append(line)
            else:
                operacoes[line.payment_information_id.payment_type] = [line]
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
            self._create_header_lote(events[0], num_lot)
            lot_sequency = 1
            for event in events:
                lot_sequency = self.create_detail(
                    lote, event, lot_sequency, num_lot)
            total_lote = self._sum_lot_values(events)
            self._create_trailer_lote(total_lote, num_lot)
            num_lot = num_lot + 1

    def _create_header_lote(self, line, num_lot):
        self._cnab_file.add_segment(
            'HeaderLote', self._get_header_lot(line, num_lot))

    def create_detail(self, operation, event, lot_sequency, num_lot):
        for segment in self.segments_per_operation().get(operation, []):
            self._cnab_file.add_segment(
                segment, self._get_segmento(event, lot_sequency, num_lot))
            lot_sequency += 1
        self._cnab_file.get_active_lot().get_active_event().close_event()
        return lot_sequency

    def segments_per_operation(self):
        return {
            "01": ["SegmentoA", "SegmentoB"],
            "02": ["SegmentoA", "SegmentoB"],
        }

    def _create_trailer_lote(self, total, num_lot):
        self._cnab_file.add_segment(
            'TrailerLote', self._get_trailer_lot(total, num_lot))
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
        return total

    def get_mes_ano_competencia(self, line):
        if not line.invoice_date:
            return 0
        date = datetime.strptime(line.invoice_date, "%Y-%m-%d")
        return int('{}{}'.format(date.month, date.year))
