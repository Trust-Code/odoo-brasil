import re

URLS = {
    1: "https://apphom.correios.com.br/SigepMasterJPA/AtendeClienteService/AtendeCliente?wsdl",
    2: "https://apps.correios.com.br/SigepMasterJPA/AtendeClienteService/AtendeCliente?wsdl",
    "PrecoPrazo": "http://ws.correios.com.br/calculador/CalcPrecoPrazo.asmx?wsdl",
}

CARACTERES_NUMERICOS = re.compile(r'[^0-9]')

regex_map = {
    'codAdministrativo': {
        'regex': r'^\d{8}$',
        'msg_erro': 'Código Adminsitrativo deve ser formado apenas por números e conter 8 digitos.',
    },
    'idContrato': {
        'regex': r'^\d{10}$',
        'msg_erro': 'ID do contrato deve ser formado apenas por números e conter 10 digitos.',
    },
    'idCartaoPostagem': {
        'regex': r'^\d{10}$',
        'msg_erro': 'ID do cartão de postagem deve ser formado apenas por números e conter 10 digitos.',
    },
    'numeroServico': {
        'regex': r'^\d{5}$',
        'msg_erro': 'Código do Serviço deve ser formado apenas por números e conter 5 digitos.',
    },
    'cep': {
        'regex': r'^\d{8}$',
        'msg_erro': 'CEP mal formatado. CEP deve conter 8 digitos.',
    },
    'numeroCartaoPostagem': {
        'regex': r'^\d{10}$',
        'msg_erro': 'Numero do cartão de postagem deve conter 10 digitos.',
    },
    'tipoDestinatario': {
        'regex': r'^\w{1}$',
        'msg_erro': 'Tipo de destinatario incorreto.',
    },
    'cnpj': {
        'regex': r'^\d{14}$',
        'msg_erro': 'CNPJ inválido.',
    },
    'etiqueta': {
        'regex': r'^[A-Z]{2}\d{8} BR$',
        'msg_erro': 'Etiqueta inválida. A etiqueta deve possuir 13 caracters e ser do formato: "AA00000000 BR"'
    }
}


def validar(key, string):
    """Realiza a validação de uma dado texto a partir da regex fornecida.

    Arguments:
        regex {str} -- Expressao regular para ser utilizada na validacao.
        string {str} -- Texto a ser validado.
        msg_erro {Str} -- Mensagem de erro.

    Raises:
        ValueError -- Quando a string fornecida não coincide com sua expressão regular.
    """

    if not re.search(regex_map[key]['regex'], string):
        raise ValueError(regex_map[key]['msg_erro'])


def trim(string):
    """Remove pontuações da string, deixando apenas valores númericos.

    Arguments:
        string {str} -- String a ser formatada.

    Returns:
        str -- Nova string formatada.
    """

    return CARACTERES_NUMERICOS.sub('', string)


def gera_digito_verificador(etiquetas):
    """Algoritmo para geração do dígito verificador.

    Arguments:
        etiquetas {list} -- Lista de etiquetas sem digito verificador.

    Raises:
        ValueError -- Caso a etiqueta contenha menos de 12 caracteres.

    Returns:
        list -- lista contendo os digitos verificadores (int).
    """

    lista_dv = []
    multiplicadores = [8, 6, 4, 2, 3, 5, 9, 7]

    for etiqueta in etiquetas:

        # Removemos espaco em branco do numero da etiqueta
        numero = etiqueta[2:10].strip()

        if len(etiqueta) != 13:
            raise ValueError('Etiqueta %s deve possir tamanho 13. Tamanho encontrado: %d' % (etiqueta,
                                                                                             len(etiqueta)))

        retorno = numero.zfill(8) if len(numero) < 8 else numero

        resto = sum([int(retorno[i:i + 1]) * multiplicadores[i] for i in range(8)]) % 11

        if resto == 0:
            dv = 5
        elif resto == 1:
            dv = 0
        else:
            dv = int(11 - resto)

        lista_dv.append(dv)

    return lista_dv
