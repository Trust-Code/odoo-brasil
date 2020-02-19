# © 2016 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

CST_ICMS = [
    ('00', '00 - Tributada Integralmente'),
    ('10', '10 - Tributada e com cobrança do ICMS por substituição tributária'),  # noqa
    ('20', '20 - Com redução de base de cálculo'),
    ('30', '30 - Isenta ou não tributada e com cobrança do ICMS por substituição tributária'),  # noqa
    ('40', '40 - Isenta'),
    ('41', '41 - Não tributada'),
    ('50', '50 - Suspensão'),
    ('51', '51 - Diferimento'),
    ('60', '60 - ICMS cobrado anteriormente por substituição tributária'),
    ('70', '70 - Com redução de base de cálculo e cobrança do ICMS por substituição tributária'),  # noqa
    ('90', '90 - Outras')
]

CSOSN_SIMPLES = [
    ('101', '101 - Tributada pelo Simples Nacional com permissão de crédito'),
    ('102', '102 - Tributada pelo Simples Nacional sem permissão de crédito'),
    ('103', '103 -Isenção do ICMS no Simples Nacional para faixa de receita bruta'),  # noqa
    ('201', '201 - Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por substituição tributária'),  # noqa
    ('202', '202 - Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por substituição tributária'),  # noqa
    ('203', '203 - Isenção do ICMS no Simples Nacional para faixa de receita bruta e com cobrança do ICMS por substituição tributária'),  # noqa
    ('300', '300 - Imune'),
    ('400', '400 - Não tributada pelo Simples Nacional'),
    ('500', '500 - ICMS cobrado anteriormente por substituição tributária (substituído) ou por antecipação'),  # noqa
    ('900', '900 - Outros')
]

ORIGEM_PROD = [
    ('0', '0 - Nacional'),
    ('1', '1 - Estrangeira - Importação direta'),
    ('2', '2 - Estrangeira - Adquirida no mercado interno'),
    ('3', '3 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 40% e inferior ou igual a 70%'),  # noqa
    ('4', '4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos de que tratam as legislações citadas nos Ajustes'),  # noqa
    ('5', '5 - Nacional, mercadoria ou bem com Conteúdo de Importação inferior ou igual a 40%'),  # noqa
    ('6', '6 - Estrangeira - Importação direta, sem similar nacional, constante em lista da CAMEX e gás natural'),  # noqa
    ('7', '7 - Estrangeira - Adquirida no mercado interno, sem similar nacional, constante lista CAMEX e gás natural'),  # noqa
    ('8', '8 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 70%')  # noqa
]

CST_IPI = [
    ('00', '00 - Entrada com Recuperação de Crédito'),
    ('01', '01 - Entrada Tributável com Alíquota Zero'),
    ('02', '02 - Entrada Isenta'),
    ('03', '03 - Entrada Não-Tributada'),
    ('04', '04 - Entrada Imune'),
    ('05', '05 - Entrada com Suspensão'),
    ('49', '49 - Outras Entradas'),
    ('50', '50 - Saída Tributada'),
    ('51', '51 - Saída Tributável com Alíquota Zero'),
    ('52', '52 - Saída Isenta'),
    ('53', '53 - Saída Não-Tributada'),
    ('54', '54 - Saída Imune'),
    ('55', '55 - Saída com Suspensão'),
    ('99', '99 - Outras Saídas')
]

CST_PIS_COFINS = [
    ('01', '01 - Operação Tributável com Alíquota Básica'),
    ('02', '02 - Operação Tributável com Alíquota Diferenciada'),
    ('03', '03 - Operação Tributável com Alíquota por Unidade de Medida de Produto'),  # noqa
    ('04', '04 - Operação Tributável Monofásica - Revenda a Alíquota Zero'),
    ('05', '05 - Operação Tributável por Substituição Tributária'),
    ('06', '06 - Operação Tributável a Alíquota Zero'),
    ('07', '07 - Operação Isenta da Contribuição'),
    ('08', '08 - Operação sem Incidência da Contribuição'),
    ('09', '09 - Operação com Suspensão da Contribuiçã'),
    ('49', '49 - Outras Operações de Saída'),
    ('50', '50 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),  # noqa
    ('51', '51 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno'),  # noqa
    ('52', '52 - Operação com Direito a Crédito - Vinculada Exclusivamente a Receita de Exportação'),  # noqa
    ('53', '53 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),  # noqa
    ('54', '54 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),  # noqa
    ('55', '55 - Operação com Direito a Crédito - Vinculada a Receitas Não Tributadas no Mercado Interno e de Exportação'),  # noqa
    ('56', '56 - Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno e de Exportação'),  # noqa
    ('60', '60 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),  # noqa
    ('61', '61 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno'),  # noqa
    ('62', '62 - Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação'),  # noqa
    ('63', '63 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),  # noqa
    ('64', '64 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),  # noqa
    ('65', '65 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação'),  # noqa
    ('66', '66 - Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno e de Exportação'),  # noqa
    ('67', '67 - Crédito Presumido - Outras Operações'),
    ('70', '70 - Operação de Aquisição sem Direito a Crédito'),
    ('71', '71 - Operação de Aquisição com Isenção'),
    ('72', '72 - Operação de Aquisição com Suspensão'),
    ('73', '73 - Operação de Aquisição a Alíquota Zero'),
    ('74', '74 - Operação de Aquisição sem Incidência da Contribuição'),
    ('75', '75 - Operação de Aquisição por Substituição Tributária'),
    ('98', '98 - Outras Operações de Entrada'),
    ('99', '99 - Outras Operações')
]
