# © 2018 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.addons.br_payment_cnab.tests.test_common import TestBrCnabPayment


class TestBaseCnab(TestBrCnabPayment):

    def setUp(self):
        super(TestBaseCnab, self).setUp()
        sicoob = self.env['res.bank'].search([('bic', '=', '756')])
        santander = self.env['res.bank'].search([('bic', '=', '033')])
        bradesco = self.env['res.bank'].search([('bic', '=', '237')])
        itau = self.env['res.bank'].search([('bic', '=', '341')])

        self.source_bank_accounts = self.env['res.partner.bank'].create({
            'acc_number': '84724',  # 5 digitos
            'acc_number_dig': '2',  # 1 digito
            'bra_number': '3070',  # 4 digitos
            'bra_number_dig': '0',
            'l10n_br_convenio_pagamento': '54',  # 7 digitos
            'bank_id': sicoob.id,
            'partner_id': self.main_company.partner_id.id,
            'company_id': self.main_company.id,
        })

        self.source_bank_accounts |= self.env['res.partner.bank'].create({
            'acc_number': '13000172',  # 8 digitos
            'acc_number_dig': '5',  # 1 digito
            'bra_number': '0823',  # 4 digitos
            'bra_number_dig': '',
            'l10n_br_convenio_pagamento': '004900819753',  # 12 digitos
            'bank_id': santander.id,
            'partner_id': self.main_company.partner_id.id,
            'company_id': self.main_company.id,
        })

        self.source_bank_accounts |= self.env['res.partner.bank'].create({
            'acc_number': '87388',  # 5 digitos
            'acc_number_dig': '2',  # 1 digito
            'bra_number': '0504',  # 4 digitos
            'bra_number_dig': '',
            'l10n_br_convenio_pagamento': '012345678',  # até 20 digitos
            'bank_id': bradesco.id,
            'partner_id': self.main_company.partner_id.id,
            'company_id': self.main_company.id,
        })

        self.source_bank_accounts |= self.env['res.partner.bank'].create({
            'acc_number': '22440',  # 5 digitos
            'acc_number_dig': '1',  # 1 digito
            'bra_number': '0730',  # 4 digitos
            'bra_number_dig': '',
            'l10n_br_convenio_pagamento': '00',  # 0 digitos
            'bank_id': itau.id,
            'partner_id': self.main_company.partner_id.id,
            'company_id': self.main_company.id,
        })

        numbers = {
            '756': ['84722', '84728'],
            '033': ['13000174', '13000176'],
            '237': ['87390', '87392'],
            '341': ['22442', '22444'],
        }
        self.journal_ids = self.env['account.journal']
        self.dest_bank_accounts = self.env['res.partner.bank']
        for account in self.source_bank_accounts:
            self.dest_bank_accounts |= account.copy({
                'partner_id': self.partner_fisica.id,
                'acc_number': numbers[account.bank_id.bic][0],
            })
            self.dest_bank_accounts |= account.copy({
                'partner_id': self.partner_juridica.id,
                'acc_number': numbers[account.bank_id.bic][1],
            })
            self.journal_ids |= self.env['account.journal'].create({
                'name': account.bank_id.name,
                'type': 'bank',
                'code': account.bank_id.bic,
                'bank_account_id': account.id,
                'l10n_br_sequence_nosso_numero':
                self.env['ir.sequence'].create({
                    'name': account.bank_id.name,
                }).id,
                'l10n_br_sequence_statements':
                self.env['ir.sequence'].create({
                    'name': account.bank_id.name,
                }).id,
            })

        self.ted_payment = self.env['l10n_br.payment.mode']
        self.doc_payment = self.env['l10n_br.payment.mode']
        self.titulos_payment = self.env['l10n_br.payment.mode']
        self.tributo_payment = self.env['l10n_br.payment.mode']
        self.gps_payment = self.env['l10n_br.payment.mode']
        self.fgts_payment = self.env['l10n_br.payment.mode']
        self.darf_payment = self.env['l10n_br.payment.mode']
        self.icms_gare_payment = self.env['l10n_br.payment.mode']

        for journal in self.journal_ids:
            self.ted_payment |= self.env['l10n_br.payment.mode'].create({
                'name': 'TED',
                'type': 'payable',
                'payment_type': '01',
                'service_type': '20',
                'mov_finality': '07',
                'journal_id': journal.id,
            })
            self.doc_payment |= self.env['l10n_br.payment.mode'].create({
                'name': 'DOC',
                'type': 'payable',
                'payment_type': '02',
                'service_type': '20',
                'mov_finality': '07',
                'journal_id': journal.id,
            })
            self.titulos_payment |= self.env['l10n_br.payment.mode'].create({
                'name': 'Boletos Normais',
                'type': 'payable',
                'payment_type': '03',
                'service_type': '20',
                'journal_id': journal.id,
            })
            self.tributo_payment |= self.env['l10n_br.payment.mode'].create({
                'name': 'Boletos de tributos e convenios',
                'type': 'payable',
                'payment_type': '04',
                'service_type': '22',
                'journal_id': journal.id,
            })
            self.gps_payment |= self.env['l10n_br.payment.mode'].create({
                'name': 'GPS',
                'type': 'payable',
                'payment_type': '05',
                'service_type': '22',
                'codigo_receita': '2003',  # Simples - CNPJ
                'journal_id': journal.id,
            })
            self.darf_payment |= self.env['l10n_br.payment.mode'].create({
                'name': 'DARF de IRRF',
                'type': 'payable',
                'payment_type': '06',
                'service_type': '22',
                'codigo_receita': '0561',  # IRRF - Retido na fonte
                'journal_id': journal.id,
            })
            self.fgts_payment |= self.env['l10n_br.payment.mode'].create({
                'name': 'FGTS com Código de barras',
                'type': 'payable',
                'payment_type': '08',
                'service_type': '22',
                'codigo_receita': '0181',
                'identificacao_fgts': '123456',
                'cod_recolhimento': '0181',
                'journal_id': journal.id,
            })
            self.icms_gare_payment |= self.env['l10n_br.payment.mode'].create({
                'name': 'ICMS Gare',
                'type': 'payable',
                'payment_type': '09',
                'service_type': '22',
                'codigo_receita': '046-2',
                'journal_id': journal.id,
            })

    def test_payment_mode_validation(self):
        self.env['l10n_br.payment.mode'].create(
            {'name': 'boleto', 'type': 'receivable'})
        with self.assertRaises(ValidationError):
            self.env['l10n_br.payment.mode'].create({
                'name': 'DOC',
                'type': 'payable',
                'payment_type': '01',
                'service_type': '20',
                'mov_finality': '07',
            })
        with self.assertRaises(ValidationError):
            self.env['l10n_br.payment.mode'].create({
                'name': 'DOC',
                'type': 'payable',
                'service_type': '20',
                'mov_finality': '07',
                'journal_id': self.journal_ids[0].id,
            })
        journal = self.env['account.journal'].create({
            'name': 'Diário Teste',
            'type': 'bank',
            'code': 'BNK',
        })
        with self.assertRaises(ValidationError):
            self.env['l10n_br.payment.mode'].create({
                'name': 'DOC',
                'type': 'payable',
                'service_type': '20',
                'payment_type': '01',
                'mov_finality': '07',
                'journal_id': journal.id,
            })
        journal.bank_account_id = self.env['res.partner.bank'].create({
            'acc_number': '123456',
        })
        with self.assertRaises(ValidationError):
            self.env['l10n_br.payment.mode'].create({
                'name': 'DOC',
                'type': 'payable',
                'service_type': '20',
                'payment_type': '01',
                'mov_finality': '07',
                'journal_id': journal.id,
            })

        journal.bank_account_id = self.env['res.partner.bank'].create({
            'acc_number': '658984',
            'l10n_br_convenio_pagamento': '545'
        })
        with self.assertRaises(ValidationError):
            self.env['l10n_br.payment.mode'].create({
                'name': 'DOC',
                'type': 'payable',
                'service_type': '20',
                'payment_type': '01',
                'mov_finality': '07',
                'journal_id': journal.id,
            })
