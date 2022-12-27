# © 2021 Danimar Ribeiro, Trustcode
{
    "name": "Integração Banco Itaú - Boleto Bancário",
    "version": "15.0.1.0.1",
    "category": "Finance",
    "sequence": 5,
    "author": "Code 137",
    "license": "OPL-1",
    "summary": """Realiza a integração com Boleto Bancário no Banco Itaú""",
    "website": "https://www.code137.com.br",
    "contributors": [
        "Felipe Paloschi <paloschi.eca@gmail.com>",
    ],
    "depends": [
        "l10n_br_automated_payment",
        "l10n_br_eletronic_document",
    ],
    "data": [
        "data/acquirer.xml",
        "views/payment.xml",
        "views/account_journal.xml",
        "report/boleto.xml",
    ],
    "application": True,
}
