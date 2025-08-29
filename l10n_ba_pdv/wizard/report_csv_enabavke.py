from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from .date_util import DateUtil
from .csv_util import CsvUtil as csu

class EnabavkeCSV(models.AbstractModel):
    # mora biti report.<ime_module>  ... "
    _name = 'report.l10n_ba_pdv.enabavke_csv'
    _inherit = 'report.report_csv.abstract'


    def generate_csv_report(self, writer, data, docids):

        #to je ba.pdv.wizard, jedan zapis
        #res = docids[0]
        # docids.date_from => datum od
        # docids.date_to   => datum do

        company_id = self.env['res.company'].search([('id', '=', int(data['company_id']))])
        date_from = datetime.strptime(data['date_from'], DATE_FORMAT).date()
        date_to = datetime.strptime(data['date_to'], DATE_FORMAT).date()
        enabavke_last_id = data['enabavke_last_id']
        porezni_period = data['porezni_period']

   
        # company_id.vat = PDV broj
        #company_registry = company_id.company_registry
        #company_name = company_id.name
        #company_address = company_id.street.strip()
        
        writer.writerow([
            "1", # header
            company_id.vat,
            porezni_period,
            "1", # nabavke
            "01", # prvi fajl
            DateUtil.current_date_str(),
            DateUtil.current_time_str()
        ])

        domain = []
        domain.append(('company_id', '=', company_id.id))     
        domain.append(('porezni_period', '=', porezni_period))

        # https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#odoo.models.Model.search
        nabavke = self.env['ba.pdv.nabavke'].search(domain, order="enabavke_id")

        iter_nabavke = iter(list(nabavke.ids))
        try:
            nab_id = next(iter_nabavke)
        except:
            nab_id = 0 

        ukupno = {
            "fakt_iznos_bez_pdv": 0.0,
            "fakt_iznos_sa_pdv": 0.0,
            "fakt_iznos_poljo_pausal": 0.0,
            "fakt_iznos_pdv": 0.0,
            "fakt_iznos_pdv_np": 0.0,
            "fakt_iznos_pdv_np_32": 0.0,
            "fakt_iznos_pdv_np_33": 0.0,
            "fakt_iznos_pdv_np_34": 0.0,
        }
        broj_stavki = 0
        while True:
            nabavka = self.env['ba.pdv.nabavke'].browse(nab_id)


            ukupno["fakt_iznos_bez_pdv"] += nabavka.fakt_iznos_bez_pdv
            ukupno["fakt_iznos_sa_pdv"] += nabavka.fakt_iznos_sa_pdv
            ukupno["fakt_iznos_poljo_pausal"] += nabavka.fakt_iznos_poljo_pausal
            ukupno["fakt_iznos_pdv"] += nabavka.fakt_iznos_pdv
            ukupno["fakt_iznos_pdv_np"] += nabavka.fakt_iznos_pdv_np
            ukupno["fakt_iznos_pdv_np_32"] += nabavka.fakt_iznos_pdv_np_32
            ukupno["fakt_iznos_pdv_np_33"] += nabavka.fakt_iznos_pdv_np_33
            ukupno["fakt_iznos_pdv_np_34"] += nabavka.fakt_iznos_pdv_np_34
            broj_stavki += 1
 
            writer.writerow([
                "2",
                nabavka.porezni_period,
                
                #>>> '2'.rjust(10, '0')
                #'0000000002'
                #>>> str(2).rjust(10, '0')
                #'0000000002'

                str(nabavka.enabavke_id).rjust(10, '0'),

                nabavka.tip, 
                nabavka.br_fakt,
                
                # format datuma 2025-02-03
                nabavka.dat_fakt,
                nabavka.dat_fakt_prijem,

                nabavka.dob_naz,
                nabavka.dob_sjediste,

                nabavka.dob_pdv if nabavka.dob_pdv else "",
                nabavka.dob_jib if nabavka.dob_jib else "".rjust(13, "9"),

                csu._to_csv_2_dec(nabavka.fakt_iznos_bez_pdv),
                csu._to_csv_2_dec(nabavka.fakt_iznos_sa_pdv),
                csu._to_csv_2_dec(nabavka.fakt_iznos_poljo_pausal),

                # 15 ulazni pdv
                csu._to_csv_2_dec(nabavka.fakt_iznos_pdv + nabavka.fakt_iznos_pdv_np),
                
                # 16 PDV koji se moze odbiti
                csu._to_csv_2_dec(nabavka.fakt_iznos_pdv),

                # 17 PDV koji se ne moze odbiti
                csu._to_csv_2_dec(nabavka.fakt_iznos_pdv_np),
                
                # neposlovni pdv FBiH
                csu._to_csv_2_dec(nabavka.fakt_iznos_pdv_np_32),
                # neposlovni pdv PC
                csu._to_csv_2_dec(nabavka.fakt_iznos_pdv_np_33),
                # neposlovni pdv Brcko
                csu._to_csv_2_dec(nabavka.fakt_iznos_pdv_np_34)

            ])
   

            try:
                nab_id = next(iter_nabavke)
            except:
                nab_id = 0 
 
            if nab_id == 0:
               break
           
        writer.writerow([
            "3", # footer
            
            csu._to_csv_2_dec(ukupno["fakt_iznos_bez_pdv"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_sa_pdv"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_poljo_pausal"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv"] + ukupno["fakt_iznos_pdv_np"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv_np"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv_np_32"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv_np_33"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv_np_34"]),

            round(broj_stavki, 0)

        ])

    def csv_report_options(self):
        res = super().csv_report_options()
        
        #res['fieldnames'].append('name')
        #res['fieldnames'].append('date')
        res['fieldnames'] = None

        res['delimiter'] = ';'
        #res['quoting'] = csv.QUOTE_ALL
        return res
    
