# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Vinculo entre boleto e NFe',
    'summary': """Vinculo entre boleto e NFe, permite enviar os dois
        via e-mail juntamente - Mantido por Trustcode""",
    'description': """Vinculo entre boleto e NFe - Mantido por Trustcode""",
    'version': '12.0.1.0.0',
    'category': 'account',
    'author': 'Trustcode',
    'license': 'AGPL-3',
    'website': 'http://www.trustcode.com.br',
    'contributors': [
        'Danimar Ribeiro <danimaribeiro@gmail.com>',
    ],
    'depends': [
        'br_boleto', 'br_account_einvoice'
    ],
    'data': [
        'views/res_config_settings.xml',
    ],
    'auto_install': True,
}
