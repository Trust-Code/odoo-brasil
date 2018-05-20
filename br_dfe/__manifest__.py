# -*- coding: utf-8 -*-
# © 2018 Raphael Rodrigues <raphael0608@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "br_dfe",
    'name': 'Consulta e Download de NF-e',
    'summary': 'Web Service de Distribuição de DF-e de Interesse dos Atores da NF-e (PF ou PJ)',
    'description': """Permite a Consulta e Download de Eventos e Documentos Eletrônicos
    através do Web Service do Ambiente Nacional DF-e\n
    ****** Funcionalidades inclusas******\n
    - Busca de Eventos e Documentos Eletrônicos\n
    - Manifestar um Documento Eletrônico\n
    - Busca Automática de Documentos Eletrônicos Através de Ação Agendada\n
    - Relacionamento Automático de Documentos Emitidos e Eventos Baixados""",
    'version': '11.0.1.0.0',
    'category': 'account',
    'author': 'Raphael Rodrigues, <raphael0608@gmail.com>',
    'license': 'AGPL-3',
    'contributors': [
        'Raphael Rodrigues <raphael0608@gmail.com>',
    ],
    'depends': [
        'br_nfe',
    ],
    'external_dependencies': {
        'python': [
            'pytrustnfe', 'pytrustnfe.nfe',
            'pytrustnfe.certificado', 'pytrustnfe.utils'
        ],
    },

    'data': [
        # 'security/ir.model.access.csv',
        'views/br_dfe.xml',
        'views/templates.xml',
        'data/search_events.xml',
    ],
    'installable': True,
}