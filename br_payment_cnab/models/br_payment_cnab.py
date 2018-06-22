# -*- coding: utf-8 -*-
# © 2018 Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# from ..febraban.cnab import Cnab
from odoo import models, fields, api

# campo novo para decidir modo de pagamento
# deve ser adicionado ao account.voucher


class PaymentCnabInformation(models.Model):
    _name = 'l10n_br.payment_cnab'

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s" % (rec.mov_finality or '')))
        return result

    mov_finality = fields.Selection([
        ('01', u'Current Account Credit'),
        ('02', u'Rent Payment/Condominium'),
        ('03', u'Dept Security Payment'),
        ('04', u'Dividend Payment'),
        ('05', u'Tuition Payment'),
        ('07', u'Provider/Fees Payment'),
        ('08', u'Currency Exchange/Fund/Stock Exchange Payment'),
        ('09', u'Transfer of Collection / Payment of Taxes'),
        ('11', u'DOC/TED to Saving Account'),
        ('12', u'DOC/TED to Judicial Deposit'),
        ('13', u'Child Support/Alimony'),
        ('14', u'Income Tax Rebate'),
        ('99', u'Other')
        ], string=u'Movimentation Purpose', required=True)

    operation_code = fields.Selection([     # G14
        ('018', u'TED CIP'),
        ('810', u'TED STR'),
        ('700', u'DOC'),
        ('000', u'CC')
    ], string=u'Operation Code')

    entry_mode = fields.Selection([('01', u'Current Account Credit'),
                                   ('03', 'Transfer to Other Banks (DOC, TED CIP e TED STR)'),
                                   ('05', 'Saving Account Credit'),
                                   ('10', 'Payment Order/acquittance'),
                                   ('11', 'Barcode paymet'),  # ajeitar
                                   ('16', 'regular DARF'),  # traduzir daqui pra baixo - se necessário
                                   ('17', 'GPS - Guia de previdencia Social'),
                                   ('18', 'Simple DARF'),
                                   ('20', '"caixa" Autentication'),
                                   ('22', 'GARE SP ICMS'),
                                   ('23', 'GARE SP DR'),
                                   ('24', 'GARE SP ITCMD'),
                                   ('25', 'IPVA SP'),
                                   ('26', 'LICENCIAMENTO SP'),
                                   ('27', 'DPVAT SP')], string="Entry mode")

    warning_code = fields.Selection([
        ('0', u'No Warning'),
        ('2', u'Warning only for addresser'),
        ('5', u'Warning only for receiver'),
        ('6', u'Warning for both, addresser and receiver')
    ], string='Warning Code', default='0')

    lote_serv = fields.Integer('Order of Service')

    reg_type = fields.Integer('Register Type')

    mov_type = fields.Selection([('0', 'Inclusion'),
                                ('5', 'Modification'),
                                ('9', 'Exclusion')],
                                string='Movimentation Type', default='0')

    mov_instruc = fields.Selection([ 
                                ('00', 'Inclusion of Released Detail Register'),
                                ('09', 'Inclusion of Blocked Detail Register(Pending Authorization)'),
                                ('10', 'Payment Modification - Released to Blocked'),
                                ('11', 'Payment Modification - Blocked to Released'),
                                ('14', 'Payment Authorization'),
                                ('33', 'Refund Chargeback')
                                ], string='Movimentation Instrution',
                                   default='00')

    serv_type = fields.Selection([('03', 'Bloqueto Eletronico'),
                                  ('10', 'pagamento de dividendos'),
                                  ('14', 'Consulta de tributos a pagar DETRAN com RENAVAM'),
                                  ('20', 'Provider/Fees Payment'),
                                  ('22', 'bill and tax payment'),
                                  ('29', 'alegacao do sacado'),
                                  ('50', 'pagamento de sinistros segurados'),
                                  ('60', 'Pagamento Despesas Viajante em Transito'),
                                  ('70', 'Pagamento Autorizado'),
                                  ('75', 'Pagamento Credenciados'),
                                  ('80', 'Pagamento Representantes / Vendedores Autorizados'),
                                  ('90', 'Pagamento Beneficios'),
                                  ('98', 'Pagamentos Diversos')
                                  ], string='Service Type')

    message2 = fields.Char(string='Note Detail', size=40)

    # variaveis para o header arquivo

    # variaveis para o header de lote

    message1 = fields.Char(string='Note Header', size=40)


class PaymentOrderLine(models.Model):
    _inherit = 'payment.order.line'

    other_payment = fields.Many2one('l10n_br.payment_cnab',
                                    string="Other Payment Information")
