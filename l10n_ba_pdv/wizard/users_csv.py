# partner_csv_report.py
from odoo import models

import csv
from odoo import models
class UsersCSV(models.AbstractModel):    

    # mora biti report.<ime_module>  ... "
    _name = "report.l10n_ba_pdv.users_csv"
    _inherit = 'report.report_csv.abstract'
    _description = "Report Users to CSV"
    
    def generate_csv_report(self, writer, data, partners):
        writer.writeheader()
        for obj in partners:
            writer.writerow({
                'name': obj.name,
                'email': obj.email,  
            })
    def csv_report_options(self):
        res = super().csv_report_options()
        res['fieldnames'].append('name')
        res['fieldnames'].append('email')
        res['delimiter'] = ';'
        res['quoting'] = csv.QUOTE_ALL
        return res