from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

class PdvNabavke(models.Model):

    _name = 'ba.pdv.nabavke'
    _description = 'PDV eNabavke'

    company_id = fields.Many2one(
        "res.company",
        string="Preduzeće",
        required=True,
        default=lambda self: self.env.company,
    )
    enabavke_id = fields.Integer(string="Redni broj nabavke", required=True, Index=True)
    porezni_period = fields.Char(string="Porezni period", size=4, required=True)
    br_fakt = fields.Char(string="Broj fakture")
    dat_fakt = fields.Date(string="Datum Fakture")
    dat_fakt_prijem = fields.Date(string="Datum prijema fakture")
    dob_naz = fields.Char(string="Naziv dobavljača")
    dob_sjediste = fields.Char(string="Sjedište dobavljača")
    dob_pdv = fields.Char(string="PDV broj", size=12)
    dob_jib = fields.Char(string="Identifikacioni broj dobavljača")
    fakt_iznos_bez_pdv = fields.Float(string="Fakt iznos bez PDV", digits=(12,2), default=0.0)
    fakt_iznos_sa_pdv = fields.Float(string="Fakt iznos sa PDV", digits=(12,2), default=0.0)
    fakt_iznos_poljo_pausal = fields.Float(string="Fakt iznos bez PDV", digits=(12,2), default=0.0)
    fakt_iznos_pdv = fields.Float(string="Fakt iznos PDV", digits=(12,2), default=0.0)
    fakt_iznos_pdv_np = fields.Float(string="Fakt iznos PDV neposlovno - krajnja potrošnja", digits=(12,2), default=0.0)
    fakt_iznos_pdv_np_32 = fields.Float(string="Fakt iznos PDV neposlovno - krajnja potrošnja FBiH", digits=(12,2), default=0.0)
    fakt_iznos_pdv_np_33 = fields.Float(string="Fakt iznos PDV neposlovno - krajnja potrošnja PC", digits=(12,2), default=0.0)
    fakt_iznos_pdv_np_34 = fields.Float(string="Fakt iznos PDV neposlovno - krajnja potrošnja BD", digits=(12,2), default=0.0)
    move_id = fields.Many2one(
        "account.move",
        string="Fin nalog",
        readonly=True,
        check_company=True,
    )
    tip = fields.Char(string="Tip nabavke", size=2)

    _sql_constraints = [
        (
            "enabavke_unique_id",
            "unique(company_id, enabavke_id)",
            "Redni broj enabavke je jedinstven.",
        ),
        #(
        #    "coin_amount_positive",
        #    "CHECK(coin_amount >= 0)",
        #    "The loose coin amount must be positive or null.",
        #),
    ]

    def get_last_number(self, date_from):

        self._cr.execute("""
            select max(enabavke_id) 
                FROM ba_pdv_nabavke
                WHERE porezni_period<'%s'
            """ % ( self._get_porezni_period(date_from) ))
        num = self._cr.fetchone()[0]
        return num

    def _get_porezni_period(self, dat_od: datetime.date):
        # 2502 - februart 2025

        return dat_od.strftime("%y%m")

    def _delete_existing(self, porezni_period: str):

        records = self.search(
            [
                ("porezni_period", "=", porezni_period)
            ]
        )
        records.unlink()



    def generate_enabavke(self, company_id: int, dat_od: datetime.date, dat_do: datetime.date, enabavke_last_id: int, regenerate=True):
        
        porezni_period = self._get_porezni_period(dat_od)

        if regenerate:
            self._delete_existing(porezni_period)

        domain = [] 
        domain.append(('company_id', '=', company_id.id))
        domain.append(('date', '>=', dat_od))
        domain.append(('date', '<=', dat_do))
        domain.append(('state', '=', 'posted'))   
        domain.append(('move_type', 'in', ['in_invoice', 'in_refund']))

        moves = self.env['account.move'].search(domain, order="date, name")

        iter_moves = iter(list(moves.ids))
        try:
            move_id = next(iter_moves)
        except:
            move_id = 0 

        enabavke_id = enabavke_last_id + 1
        while move_id != 0:
            move = self.env['account.move'].browse(move_id)
            
            print(move.name)

            fakt_iznos_bez_pdv = 0
            fakt_iznos_pdv = 0
            fakt_iznos_pdv_np = 0
            fakt_iznos_pdv_np_32 = 0
            fakt_iznos_pdv_np_33 = 0
            fakt_iznos_pdv_np_34 = 0

            #move.partner_id

            # move.partner_id.country_id.code == 'BA'
            
            # krajnja potrosnja 32 - FBiH, 33 - PC, 34 - BD
            kp = 32

        
            # kod ulaznih racuna gleda se mjesto potrosnje
            # npr. ako preduzeće ima poslovnice u drugom entitetu, onda potrošnja u tim poslovnicama ide na taj entitet

            #if move.partner_id.state_id:
            #    if move.partner_id.state_id.code == "RS":
            #        kp = 33
            #    elif move.partner_id.state_id.code == "BD":
            #        kp = 34

            if move.company_id.state_id.code == "RS":
                kp = 33
            elif move.company_id.state_id.code == "BD":
                kp = 34

            for move_line in move.line_ids:
                for tag in move_line.tax_tag_ids:
                    # partner_id
                    # tax_audit
                    # move_name
                    if tag.name in ("P21", "P21_KP"):
                        # osnovica pdv
                        fakt_iznos_bez_pdv += move_line.amount_currency
                    if tag.name == "P41":
                        fakt_iznos_pdv += move_line.amount_currency
                    if tag.name == "P44":
                        fakt_iznos_pdv_np += move_line.amount_currency
                        if kp == 32:
                            fakt_iznos_pdv_np_32 += move_line.amount_currency
                        elif kp == 33:
                            fakt_iznos_pdv_np_33 += move_line.amount_currency
                        elif kp == 34:
                            fakt_iznos_pdv_np_34 += move_line.amount_currency


            # moze biti 01 - poslovna potrošnja ili 02 - vanposlovna potrošnja (benzin u preduzeću koje nije prevoznik, reprezentracija)
            _tip_nabavka = "02" if (abs(fakt_iznos_pdv_np) > abs(fakt_iznos_pdv)) else "01"
            
            if move.is_partner_ino_usluge():
                _tip_nabavka = "05"

            if (round(fakt_iznos_bez_pdv, 2) == 0.0 and 
                round(fakt_iznos_bez_pdv + fakt_iznos_pdv + fakt_iznos_pdv_np, 2) == 0.0
               ):
               try:
                    move_id = next(iter_moves)
               except:
                    move_id = 0 
               move = self.env['account.move'].browse(move_id)
               continue

            self.env["ba.pdv.nabavke"].create({
                "enabavke_id": enabavke_id,
                "porezni_period": porezni_period,
                "br_fakt": move.ref,
                "dat_fakt": move.invoice_date,
                "dat_fakt_prijem": move.date,
                "dob_naz": move.partner_id.display_name,
                "dob_sjediste": (move.partner_id.zip or "") + " " + (move.partner_id.city or "") + " " + (move.partner_id.street or ""),
                "dob_pdv": move.partner_id.vat,
                "dob_jib": move.partner_id.company_registry,
                "fakt_iznos_bez_pdv": round(fakt_iznos_bez_pdv, 2),
                "fakt_iznos_sa_pdv": round(fakt_iznos_bez_pdv + fakt_iznos_pdv + fakt_iznos_pdv_np, 2),
                "fakt_iznos_poljo_pausal": 0.0,
                "fakt_iznos_pdv": round(fakt_iznos_pdv, 2),
                "fakt_iznos_pdv_np": round(fakt_iznos_pdv_np, 2),
                "fakt_iznos_pdv_np_32": round(fakt_iznos_pdv_np_32, 2),
                "fakt_iznos_pdv_np_33": round(fakt_iznos_pdv_np_33, 2),
                "fakt_iznos_pdv_np_34": round(fakt_iznos_pdv_np_34, 2),
                "tip": _tip_nabavka,
                "move_id": move.id
            })

            enabavke_id += 1

            try:
                move_id = next(iter_moves)
            except:
                move_id = 0 
            move = self.env['account.move'].browse(move_id)

        return porezni_period 






