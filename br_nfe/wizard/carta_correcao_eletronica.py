# -*- coding: utf-8 -*-
# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import api, fields, models
from pytrustnfe.nfe import carta_correcao_eletronica


class CartaCorrecaoEletronica(models.TransientModel):
    _name = 'wizard.carta.correcao.eletronica'

    correcao = fields.Text(string="Correção", max_length=1000)
    invoice_id = fields.Many2one('invoice.eletronic')
    dh_evento = fields.Datetime(string="Data e Hora da Correção")

    @api.multi
    def send_letter(self):
        self.invoice_id = self._context['invoice_id']
        # TODO: idLote, cOrgao, Id, nSeqEvento, detEvento
        self.dh_evento = datetime.now()
        chave_nfe = self.invoice_id.serie
        ambiente = self.invoice_id.company_id.tipo_ambiente
        cnpj = self.env.user.cnpj_cpf
        dh_evento = self.dh_evento
        tp_evento = '110110'
        desc_evento = 'Carta de Correção'
        x_correcao = self.correcao
