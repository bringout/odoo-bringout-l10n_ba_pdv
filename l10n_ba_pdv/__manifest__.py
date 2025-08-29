{
    'name': 'PDV obračun Bosna i Hercegovina',
    'version': '1.1.1',
    'author': "bring.out Sarajevo, BiH",
    'sequence': 190,
    'summary': 'Bosnian obračun PDV',
    'depends': ["account", "l10n_bs", "report_xlsx", "report_csv"],
    'data': [
        "reports/ba_pdv_xlsx.xml",
        "views/ba_pdv_wizard_view.xml",
        "views/menus.xml",

        "security/ir.model.access.csv",
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
