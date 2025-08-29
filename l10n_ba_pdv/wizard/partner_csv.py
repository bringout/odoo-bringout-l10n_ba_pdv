# partner_csv_report.py
from odoo import models

import csv
from odoo import models
class PartnerCSV2(models.AbstractModel):
    _name = "report.l10n_ba_pdv.partner_csv_2"
    _inherit = "report.report_csv.abstract"
    _description = "Report Partner to CSV 2"

    def generate_csv_report(self, writer, data, partners):
        writer.writeheader()
        for obj in partners:
            writer.writerow({
                'name2': obj.name,
                'email2': obj.email,  
            })
    def csv_report_options(self):
        res = super().csv_report_options()
        res['fieldnames'].append('name2')
        res['fieldnames'].append('email2')
        res['delimiter'] = ';'
        res['quoting'] = csv.QUOTE_ALL
        return res