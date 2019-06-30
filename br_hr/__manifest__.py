# © 2014 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{  # pylint: disable=C8101,C8103
    'name': 'Brazilian Localization HR',
    'description': """Brazilian Localization HR with informations
        refered to the national context of HR""",
    'category': 'Localization',
    'author': 'KMEE',
    'sequence': 45,
    'maintainer': 'Trustcode',
    'website': 'http://www.trustcode.com.br/',
    'version': '12.0.1.0.0',
    'depends': ['hr', 'br_base'],
    'data': [
        'data/br_hr.cbo.csv',
        'security/ir.model.access.csv',
        'view/br_hr_cbo_view.xml',
        'view/hr_employee_view.xml',
        'view/hr_job_view.xml',
    ],
    'post_init_hook': 'post_init',
    'installable': True,
    'license': 'AGPL-3',
}
