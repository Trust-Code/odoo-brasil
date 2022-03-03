# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import api, fields, models


class EletronicDocument(models.Model):
    _inherit = 'eletronic.document'

    pos_order_id = fields.Many2one(
        'pos.order', string=u'Pedido POS', readonly=True)
    customer_cpf = fields.Char(string='CPF')

    def _get_variables_msg(self):
        variables = super(EletronicDocument, self)._get_variables_msg()
        variables.update({
            'order': self.pos_order_id,
            'eletronic': self
        })
        return variables

    def _prepare_eletronic_invoice_values(self):
        vals = super(EletronicDocument, self)\
            ._prepare_eletronic_invoice_values()
        if self.model != '65':
            return vals
        vals['pag'][0]['tPag'] = self.metodo_pagamento
        vals['pag'][0]['vPag'] = "%.02f" % self.valor_pago
        vals['pag'][0]['vTroco'] = "%.02f" % self.troco or '0.00'
        if self.customer_cpf:
            vals.update({
                'dest': {
                        'tipo': 'person',
                        'cnpj_cpf': re.sub('[^0-9]', '', self.customer_cpf),
                        'xNome': u'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO -\
 SEM VALOR FISCAL' if self.ambiente == 'homologacao' else None,
                        'enderDest': None,
                        'indIEDest': '9'
                        }
                })
        return vals

    def _compute_legal_information(self):
        super(EletronicDocument, self)._compute_legal_information()
        if self.model != '65':
            return 
        fiscal_ids = self.pos_order_id.fiscal_position_id.\
            fiscal_observation_ids.filtered(lambda x: x.tipo == 'fiscal')
        obs_ids = self.pos_order_id.fiscal_position_id.\
            fiscal_observation_ids.filtered(lambda x: x.tipo == 'observacao')

        fiscal = self._compute_msg(fiscal_ids)

        ncm_tax_related = 'Valor Aprox. dos Tributos R$ %s. Fonte: IBPT\n' % \
                          (str(self.valor_estimado_tributos))

        observacao = ncm_tax_related + self._compute_msg(obs_ids)

        self.informacoes_legais = fiscal
        self.informacoes_complementares = observacao
