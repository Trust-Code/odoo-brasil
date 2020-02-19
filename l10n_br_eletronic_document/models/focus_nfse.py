import base64

def send_api(certificate, password, vals):
    cert_pfx = base64.decodestring(certificate)
    certificado = Certificado(cert_pfx, password)

    url = "https://homologacao.focusnfe.com.br/v2/nfse"
    token="sw9qPtcdFLAPD1XyAu84nEN4XEnfeg45"

    partner = self.commercial_partner_id

    tomador = {
        'cnpj_cpf': re.sub(
            '[^0-9]', '', partner.cnpj_cpf or ''),
        'inscricao_municipal': re.sub(
            '[^0-9]', '', partner.inscr_mun or
            '0000000'),
        'razao_social': partner.legal_name or partner.name,
        'logradouro': partner.street,
        'numero': partner.number,
        'bairro': partner.district,
        'cep': re.sub('[^0-9]', '', partner.zip or ''),
        'cidade': '%s%s' % (
            partner.state_id.ibge_code,
            partner.city_id.ibge_code),
        'uf': partner.state_id.code,
        'email': self.partner_id.email,
        'phone': re.sub('[^0-9]', '', self.partner_id.phone or ''),
    }
    items = []
    for line in self.document_line_ids:
        aliquota = line.issqn_aliquota / 100
        base = line.issqn_base_calculo
        if self.company_id.fiscal_type != '3':
            aliquota, base = 0.0, 0.0
        unitario = round(line.valor_liquido / line.quantidade, 2)
        items.append({
            'name': line.product_id.name,
            'cnae': re.sub(
                '[^0-9]', '',
                line.product_id.service_type_id.id_cnae or ''),
            'cst_servico': '1',
            'aliquota': aliquota,
            'base_calculo': base,
            'valor_unitario': unitario,
            'quantidade': int(line.quantidade),
            'valor_total': line.valor_liquido,
        })
    emissao = fields.Datetime.from_string(self.data_emissao)
    cfps = '9201'
    if self.company_id.city_id.id != partner.city_id.id:
        cfps = '9202'
    if self.company_id.state_id.id != partner.state_id.id:
        cfps = '9203'
    base, issqn = self.valor_bc_issqn, self.valor_issqn
    if self.company_id.fiscal_type != '3':
        base, issqn = 0.0, 0.0
    data = {
        'numero': "%06d" % self.numero,
        'tomador': tomador,
        'itens_servico': items,
        'data_emissao': emissao.strftime('%Y-%m-%d'),
        'base_calculo': base,
        'valor_issqn': issqn,
        'valor_total': self.valor_final,
        'aedf': self.company_id.aedf,
        'cfps': cfps,
        'observacoes': '',
    }


    ref = {"ref":"12345"}
    
    r = requests.post(url, params=ref, data=json.dumps(data), auth=(token,""))

    if r.status_code not in (200, 201):
        raise UserError(r.json()['mensagem'])
    # Mostra na tela o codigo HTTP da requisicao e a mensagem de retorno da API
    print(r.status_code, r.text)
