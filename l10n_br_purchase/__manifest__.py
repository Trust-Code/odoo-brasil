{  # pylint: disable=C8101,C8103
    "name": "Odoo Next - Purchase",
    "description": "Purchase Localization",
    "version": "13.0.1.0.0",
    "category": "Localization",
    "author": "Code 137",
    'license': 'Other OSI approved licence',
    "contributors": [
        "Johny Chen Jy <johnychenjy@gmail.com>",
        "Felipe Paloschi <paloschi.eca@gmail.com>"
    ],
    "depends": [
        "purchase", "l10n_br_account"
    ],
    'data': ["views/purchase_order.xml"],
    "auto_install": True,
}
