from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime, timedelta
from .date_util import DateUtil as du

class PdvXlsx(models.AbstractModel):

    # report.module.report_name
    _name = 'report.l10n_ba_pdv.pdv_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = "PDV xlsx"

    @api.model
    def generate_xlsx_report(self, workbook, data, data2):

        sheet_general = workbook.add_worksheet("general")
        bold = workbook.add_format({'bold': True})

        percent_fmt = workbook.add_format({'num_format': '0.0%'})
        
        currency_format = workbook.add_format({'num_format': '#,##0.00'})
        
        # https://xlsxwriter.readthedocs.io/worksheet.html


        # cell_format = workbook.add_format({'bold': True, 'italic': True})
        #worksheet.write(0, 0, 'Hello', cell_format)  # Cell is bold and italic.

        #worksheet.set_row(0, 70)
        sheet_general.set_column('A:A', 10)
        sheet_general.set_column('B:B', 30)

        date_format = '%Y-%m-%d'
        company_id = self.env['res.company'].search([('id', '=', int(data['company_id']))])
        date_from = data['date_from']
        date_to = data['date_to']
 
        # company_id.vat = PDV broj
        company_registry = company_id.company_registry
        company_vat = company_id.vat

        company_name = company_id.name
        #company_address = company_id.street.strip()
        
        period_od = datetime.strptime(date_from, date_format).date()
        period_do = datetime.strptime(date_to, date_format).date()
        porezni_period = data["porezni_period"]

        
        #porezna_godina = period_do.year
        row = 0
        col = 0
        sheet_general.write(row, col, f"Preduzeće: {company_name} ID: {company_registry} PDV: {company_vat}")
        row += 2
        sheet_general.write(row, col, f"Porezni period: {porezni_period}")
        row += 2
        sheet_general.write(row, col, f"Period: {du.date_str(period_od)} - {du.date_str(period_do)}")
        
        self._enabavke(workbook, data, data2)
        self._eisporuke(workbook, data, data2)



    def _enabavke(self, workbook, data, data2):

        currency_format = workbook.add_format({'num_format': '#,##0.00'})
        bold = workbook.add_format({'bold': True})

        company_id = self.env['res.company'].search([('id', '=', int(data['company_id']))])
        date_from = datetime.strptime(data['date_from'], DATE_FORMAT).date()
        date_to = datetime.strptime(data['date_to'], DATE_FORMAT).date()
        enabavke_last_id = data['enabavke_last_id']

        # generisi enabavke
        porezni_period = self.env['ba.pdv.nabavke'].generate_enabavke(company_id, date_from, date_to, enabavke_last_id=enabavke_last_id, regenerate=True)
 
        sheet_nab = workbook.add_worksheet("enabavke")

        row = 0
        col = 0
        sheet_nab.set_column('A:A', 8) 
        sheet_nab.set_column('B:B', 12)
        sheet_nab.set_column('C:C', 5) # tip
        sheet_nab.set_column('D:D', 20) # br_fakt
        sheet_nab.set_column('E:F', 12) #datumi
        sheet_nab.set_column('G:H', 40) #dob
        sheet_nab.set_column('I:J', 20) #pdv
        sheet_nab.set_column('K:S', 20)

        for header in ['por_per', 'enabavke_id', 'tip', 'br_fakt', 'dat fakt', 'dat prijem', "dobavlj naziv", "dobav sljedište", "dob_pdv", "dob_id", 
               "iznos bez PDV", "sa PDV", "polj. pausal", "PDV SVE", "PDV posl", "PDV neposl", "PDV np 32", "PDV np 33", "PDV np 34"]:
            sheet_nab.write(row, col, header, bold)
            col = col + 1

        #moves = moves.filtered(lambda x: round(x.bruto_osn_gip, ZAOKRUZENJE) > 0)


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

        row += 1
        while True:
            col = 0
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

            if nabavka.br_fakt == False or nabavka.br_fakt == '':
                if not nabavka.move_id.name:
                    break
                raise UserError(f"Broj fakture ne može biti prazan: {nabavka.move_id.name}")

            if not nabavka.dat_fakt:
                raise UserError(f"Nabavka {nabavka.move_id.name} nema datuma")

            if not nabavka.dat_fakt_prijem:
                raise UserError(f"Nabavka {nabavka.move_id.name} nema datuma")

            sheet_nab.write(row, col, nabavka.porezni_period)
            col += 1
            sheet_nab.write(row, col, str(nabavka.enabavke_id).rjust(10, '0'))
            col += 1
            sheet_nab.write(row, col, nabavka.tip)
            col += 1
            sheet_nab.write(row, col, nabavka.br_fakt)
            col += 1
            sheet_nab.write(row, col, du.date_str(nabavka.dat_fakt))
            col += 1
            sheet_nab.write(row, col, du.date_str(nabavka.dat_fakt_prijem))
            col += 1
            sheet_nab.write(row, col, nabavka.dob_naz)
            col += 1
            sheet_nab.write(row, col, nabavka.dob_sjediste)
            col += 1
            sheet_nab.write(row, col, nabavka.dob_pdv if nabavka.dob_pdv else "")
            col += 1
            sheet_nab.write(row, col, nabavka.dob_jib if nabavka.dob_jib else "".rjust(13, "9"))
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_bez_pdv, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_sa_pdv, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_poljo_pausal, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_pdv + nabavka.fakt_iznos_pdv_np, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_pdv, 2), currency_format)
            # 17 PDV koji se ne moze odbiti
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_pdv_np, 2), currency_format)
            # neposlovni pdv FBiH
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_pdv_np_32, 2), currency_format)
            # neposlovni pdv PC
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_pdv_np_33, 2), currency_format)
            # neposlovni pdv Brcko
            col += 1
            sheet_nab.write(row, col, round(nabavka.fakt_iznos_pdv_np_34, 2), currency_format)
            row += 1

            try:
                nab_id = next(iter_nabavke)
            except:
                nab_id = 0 
            
            
            if nab_id == 0:
               break
           
        #writer.writerow([
        #    "3", # footer
        #    
        #    round(ukupno["fakt_iznos_bez_pdv"], 2),
        #    round(ukupno["fakt_iznos_sa_pdv"], 2),
        #    round(ukupno["fakt_iznos_poljo_pausal"], 2),
        #    round(ukupno["fakt_iznos_pdv"] + ukupno["fakt_iznos_pdv_np"], 2),
        #    round(ukupno["fakt_iznos_pdv"], 2),
        #    round(ukupno["fakt_iznos_pdv_np"], 2),
        #    round(ukupno["fakt_iznos_pdv_np_32"], 2),
        #    round(ukupno["fakt_iznos_pdv_np_33"], 2),
        #    round(ukupno["fakt_iznos_pdv_np_34"], 2),
        #
        #    round(broj_stavki, 0)
        #
        #])

    
        
    def _eisporuke(self, workbook, data, data2):

        currency_format = workbook.add_format({'num_format': '#,##0.00'})
        bold = workbook.add_format({'bold': True})

        company_id = self.env['res.company'].search([('id', '=', int(data['company_id']))])
        date_from = datetime.strptime(data['date_from'], DATE_FORMAT).date()
        date_to = datetime.strptime(data['date_to'], DATE_FORMAT).date()
        eisporuke_last_id = data['eisporuke_last_id']

        # generisi eisporuke
        porezni_period = self.env['ba.pdv.isporuke'].generate_eisporuke(company_id, date_from, date_to, eisporuke_last_id=eisporuke_last_id, regenerate=True)
 
        sheet_nab = workbook.add_worksheet("eisporuke")

        row = 0
        col = 0
        sheet_nab.set_column('A:A', 8) 
        sheet_nab.set_column('B:B', 12)
        sheet_nab.set_column('C:C', 5) # tip
        sheet_nab.set_column('D:D', 15) #jci
        sheet_nab.set_column('E:E', 12) #dat
        sheet_nab.set_column('F:F', 15) #br_fakt
        sheet_nab.set_column('G:H', 40) #kupac
        sheet_nab.set_column('I:J', 20) #pdv, id broj
        sheet_nab.set_column('K:U', 20)
        sheet_nab.set_column('V:V', 100)

        for header in ["por_per", "eisporuke_id", "tip", "jci", "Dat.Fakt", "Br.Fakt", "kupac naziv", "kupac sljedište", "Kup.PDV", "Kup.ID", 
               "Fakt sa PDV","Fak.sa PDV interna", "Fak.sa PDV0 izvoz", "Fak sa PDV0 ostalo", "F.bez PDV", "F.PDV", "F.bez PDV NP", "F.PDV NP", "PDV np 32", "PDV np 33", "PDV np 34", "Opis"]:
            sheet_nab.write(row, col, header, bold)
            col = col + 1

        #moves = moves.filtered(lambda x: round(x.bruto_osn_gip, ZAOKRUZENJE) > 0)

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

            "fakt_iznos_pdv": 0.0,
            "fakt_iznos_pdv_np": 0.0,
            "fakt_iznos_pdv_np_32": 0.0,
            "fakt_iznos_pdv_np_33": 0.0,
            "fakt_iznos_pdv_np_34": 0.0,
        }
        broj_stavki = 0

        
        row += 1
        while True:
            col = 0
            isporuka = self.env['ba.pdv.isporuke'].browse(nab_id)

            #ukupno["fakt_iznos_bez_pdv"] += nabavka.fakt_iznos_bez_pdv
            #ukupno["fakt_iznos_sa_pdv"] += nabavka.fakt_iznos_sa_pdv

            #ukupno["fakt_iznos_pdv"] += nabavka.fakt_iznos_pdv
            #ukupno["fakt_iznos_pdv_np"] += nabavka.fakt_iznos_pdv_np
            #ukupno["fakt_iznos_pdv_np_32"] += nabavka.fakt_iznos_pdv_np_32
            #ukupno["fakt_iznos_pdv_np_33"] += nabavka.fakt_iznos_pdv_np_33
            #ukupno["fakt_iznos_pdv_np_34"] += nabavka.fakt_iznos_pdv_np_34

            broj_stavki += 1
 
            if isporuka.br_fakt == False:
                break

            if not isporuka.dat_fakt:
                raise UserError("Isporuka %s nema postavljen datum" % (isporuka.br_fakt))

            sheet_nab.write(row, col, isporuka.porezni_period)
            col += 1
            sheet_nab.write(row, col, str(isporuka.eisporuke_id).rjust(10, '0'))
            col += 1
            sheet_nab.write(row, col, isporuka.tip),
            col += 1
            sheet_nab.write(row, col, isporuka.jci),
            col += 1
            sheet_nab.write(row, col, du.date_str(isporuka.dat_fakt))
            col += 1
            sheet_nab.write(row, col, isporuka.br_fakt)
            col += 1
            sheet_nab.write(row, col, isporuka.kup_naz)
            col += 1
            sheet_nab.write(row, col, isporuka.kup_sjediste)
            col += 1
            sheet_nab.write(row, col, isporuka.kup_pdv if isporuka.kup_pdv else "")
            col += 1
            sheet_nab.write(row, col, isporuka.kup_jib if isporuka.kup_jib else "".rjust(13, "9"))
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_sa_pdv, 2), currency_format), currency_format
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_sa_pdv_interna, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_sa_pdv0_izvoz, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_sa_pdv0_ostalo, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_bez_pdv, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_pdv, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_bez_pdv_np, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_pdv_np, 2), currency_format)
            # neposlovni pdv prodavac iz FBiH
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_pdv_np_32, 2), currency_format)
            # neposlovni pdv prodavac iz PC
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_pdv_np_33, 2), currency_format)
            # neposlovni pdv prodavac iz Brcko
            col += 1
            sheet_nab.write(row, col, round(isporuka.fakt_iznos_pdv_np_34, 2), currency_format)
            col += 1
            sheet_nab.write(row, col, isporuka.opis or "")

            row += 1

            try:
                nab_id = next(iter_isporuke)
            except:
                nab_id = 0 
            
            if nab_id == 0:
               break
           

