from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from .date_util import DateUtil
from .csv_util import CsvUtil as csu

class EisporukeCSV(models.AbstractModel):
    _name = 'report.l10n_ba_pdv.eisporuke_csv'
    _inherit = 'report.report_csv.abstract'

    def _eisporuke_get_tip(self, isporuka ):
        return "01"


    def generate_csv_report(self, writer, data, docids):


        company_id = self.env['res.company'].search([('id', '=', int(data['company_id']))])
        date_from = datetime.strptime(data['date_from'], DATE_FORMAT).date()
        date_to = datetime.strptime(data['date_to'], DATE_FORMAT).date()
        porezni_period = data["porezni_period"]
        
        #eisporuke_last_id = data['eisporuke_last_id']
        # generisi eisporuke
        #porezni_period = self.env['ba.pdv.isporuke'].generate_eisporuke(company_id, date_from, date_to, eisporuke_last_id=eisporuke_last_id, regenerate=True)
 
        domain = []
        domain.append(('company_id', '=', company_id.id))     
        domain.append(('porezni_period', '=', porezni_period))

        # https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#odoo.models.Model.search
        isporuke = self.env['ba.pdv.isporuke'].search(domain, order="eisporuke_id")

        iter_isporuke = iter(list(isporuke.ids))
        try:
            nab_id = next(iter_isporuke)
        except:
            nab_id = 0 

        ukupno = {
            "fakt_iznos_sa_pdv": 0.0,
            "fakt_iznos_sa_pdv_interna": 0.0,
            "fakt_iznos_sa_pdv0_izvoz":  0.0,
            "fakt_iznos_sa_pdv0_ostalo": 0.0,

            "fakt_iznos_bez_pdv": 0.0,
            "fakt_iznos_bez_pdv_np": 0.0,

            "fakt_iznos_pdv": 0.0,
            "fakt_iznos_pdv_np": 0.0,
            "fakt_iznos_pdv_np_32": 0.0,
            "fakt_iznos_pdv_np_33": 0.0,
            "fakt_iznos_pdv_np_34": 0.0,
        }
        broj_stavki = 0

        writer.writerow([
            "1", # header
            company_id.vat,
            porezni_period,
            "2", # isporuke
            "01", # prvi fajl
            DateUtil.current_date_str(),
            DateUtil.current_time_str()
        ])

        while True:
            col = 0
            isporuka = self.env['ba.pdv.isporuke'].browse(nab_id)

     
            ukupno["fakt_iznos_sa_pdv"] += isporuka.fakt_iznos_sa_pdv
            ukupno["fakt_iznos_sa_pdv_interna"] += isporuka.fakt_iznos_sa_pdv_interna
            ukupno["fakt_iznos_sa_pdv0_izvoz"]  += isporuka.fakt_iznos_sa_pdv0_izvoz
            ukupno["fakt_iznos_sa_pdv0_ostalo"] += isporuka.fakt_iznos_sa_pdv0_ostalo

            ukupno["fakt_iznos_bez_pdv"] += isporuka.fakt_iznos_bez_pdv
            ukupno["fakt_iznos_pdv"] += isporuka.fakt_iznos_pdv

            ukupno["fakt_iznos_bez_pdv_np"] += isporuka.fakt_iznos_bez_pdv_np
            ukupno["fakt_iznos_pdv_np"] += isporuka.fakt_iznos_pdv_np
            ukupno["fakt_iznos_pdv_np_32"] += isporuka.fakt_iznos_pdv_np_32
            ukupno["fakt_iznos_pdv_np_33"] += isporuka.fakt_iznos_pdv_np_33
            ukupno["fakt_iznos_pdv_np_34"] += isporuka.fakt_iznos_pdv_np_34

            broj_stavki += 1

            writer.writerow([
                "2",
                isporuka.porezni_period,
                str(isporuka.eisporuke_id).rjust(10, '0'),
                self._eisporuke_get_tip(isporuka),
                isporuka.br_fakt,
                
                # format datuma 2025-02-03
                isporuka.dat_fakt,
             

                isporuka.kup_naz,
                isporuka.kup_sjediste,

                isporuka.kup_pdv if isporuka.kup_pdv else "",
                isporuka.kup_jib if isporuka.kup_jib else "".rjust(13, "9"),


                csu._to_csv_2_dec(isporuka.fakt_iznos_sa_pdv),
                csu._to_csv_2_dec(isporuka.fakt_iznos_sa_pdv_interna),
                csu._to_csv_2_dec(isporuka.fakt_iznos_sa_pdv0_izvoz),
                csu._to_csv_2_dec(isporuka.fakt_iznos_sa_pdv0_ostalo),
 
                # pdv obveznici
                csu._to_csv_2_dec(isporuka.fakt_iznos_bez_pdv),
                csu._to_csv_2_dec(isporuka.fakt_iznos_pdv),

                # ne pdv obveznici
                csu._to_csv_2_dec(isporuka.fakt_iznos_bez_pdv_np),
                csu._to_csv_2_dec(isporuka.fakt_iznos_pdv_np),
                # nepdv obveznici FBiH
                csu._to_csv_2_dec(isporuka.fakt_iznos_pdv_np_32),
                # PC
                csu._to_csv_2_dec(isporuka.fakt_iznos_pdv_np_33),
                # Brcko
                csu._to_csv_2_dec(isporuka.fakt_iznos_pdv_np_34)

            ])
 
            try:
                nab_id = next(iter_isporuke)
            except:
                nab_id = 0 
            
            if nab_id == 0:
               break

        writer.writerow([
            "3", # footer
    
            csu._to_csv_2_dec(ukupno["fakt_iznos_sa_pdv"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_sa_pdv_interna"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_sa_pdv0_izvoz"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_sa_pdv0_ostalo"]),
            
            csu._to_csv_2_dec(ukupno["fakt_iznos_bez_pdv"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv"]),

            csu._to_csv_2_dec(ukupno["fakt_iznos_bez_pdv_np"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv_np"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv_np_32"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv_np_33"]),
            csu._to_csv_2_dec(ukupno["fakt_iznos_pdv_np_34"]),

            round(broj_stavki, 0)
        ])    

    def csv_report_options(self):
        res = super().csv_report_options()
        res['fieldnames'] = None
        res['delimiter'] = ';'
        return res