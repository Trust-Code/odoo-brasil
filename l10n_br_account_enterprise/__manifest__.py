# © 2021 Danimar Ribeiro, Trustcode
# Part of Trustcode. See LICENSE file for full copyright and licensing details.

{  # pylint: disable=C8101,C8103
    "name": "Odoo Brasil - Account Enterprise",
    "description": "Enable advanced tax management",
    "version": "16.0.1.0.0",
    "category": "Localization",
    "author": "Trustcode",
    "license": "Other OSI approved licence",
    "website": "http://www.trustcode.com,br",
    "contributors": [
        "Danimar Ribeiro <danimaribeiro@gmail.com>",
    ],
    "depends": [
        "l10n_br_account",
        "l10n_br_base",
        "l10n_br_base_address",
        "l10n_br_eletronic_document",
        "l10n_br_sale",
        "l10n_br_purchase",
    ],
    "data": [
        "data/account_accountant.xml",
        "views/account_fiscal_position.xml",
        "views/account_move.xml",
        "views/sale_order.xml",
        "views/purchase.xml",
    ],
}
