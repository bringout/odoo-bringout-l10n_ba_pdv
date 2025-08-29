from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

class PdvIsporuke(models.Model):

    _name = 'ba.pdv.isporuke'
    _description = 'PDV Isporuke'

    
    company_id = fields.Many2one(
        "res.company",
        string="Preduzeće",
        required=True,
        default=lambda self: self.env.company,
    )

    eisporuke_id = fields.Integer(string="Redni broj isporuke", required=True, Index=True)
    porezni_period = fields.Char(string="Porezni period", size=4, required=True)
    tip = fields.Char(string="Tip isporuke", size=2)
    br_fakt = fields.Char(string="Broj fakture")
    dat_fakt = fields.Date(string="Datum Fakture")

    kup_naz = fields.Char(string="Naziv kupca")
    kup_sjediste = fields.Char(string="Sjedište kupca")
    kup_pdv = fields.Char(string="PDV broj", size=12)
    kup_jib = fields.Char(string="Identifikacioni broj kupca")
    
    fakt_iznos_sa_pdv = fields.Float(string="Fakt iznos sa PDV", digits=(12,2), default=0.0)
    fakt_iznos_sa_pdv_interna = fields.Float(string="Fakt iznos sa PDV", digits=(12,2), default=0.0)
    fakt_iznos_sa_pdv0_izvoz = fields.Float(string="Fakt iznos izvoz", digits=(12,2), default=0.0)
    fakt_iznos_sa_pdv0_ostalo = fields.Float(string="Fakt iznos sa PDV0 ostalo", digits=(12,2), default=0.0)
    fakt_iznos_bez_pdv = fields.Float(string="Fakt iznos bez PDV", digits=(12,2), default=0.0)

    fakt_iznos_pdv = fields.Float(string="Fakt iznos PDV", digits=(12,2), default=0.0)

    fakt_iznos_bez_pdv_np = fields.Float(string="Fakt iznos bez PDV Neposlovno", digits=(12,2), default=0.0)
    fakt_iznos_pdv_np = fields.Float(string="Fakt iznos PDV krajnja potrošnja", digits=(12,2), default=0.0)

    fakt_iznos_pdv_np_32 = fields.Float(string="Fakt iznos PDV neposlovno - krajnja potrošnja FBiH", digits=(12,2), default=0.0)
    fakt_iznos_pdv_np_33 = fields.Float(string="Fakt iznos PDV neposlovno - krajnja potrošnja PC", digits=(12,2), default=0.0)
    fakt_iznos_pdv_np_34 = fields.Float(string="Fakt iznos PDV neposlovno - krajnja potrošnja BD", digits=(12,2), default=0.0)
    
    opis = fields.Char(help="Opis dokumenta")
    jci = fields.Char(help="Jedinstveni carinski broj")

    move_id = fields.Many2one(
        "account.move",
        string="Fin nalog",
        readonly=True,
        check_company=True,
    )


    _sql_constraints = [
        (
            "eisporuke_unique_id",
            "unique(company_id, eisporuke_id)",
            "Redni broj eisporuke je jedinstven.",
        ),

    ]

    def get_last_number(self, date_from):

        self._cr.execute("""
            select max(eisporuke_id) 
                FROM ba_pdv_isporuke
                WHERE porezni_period<'%s'
            """ % ( self._get_porezni_period(date_from) )
        )
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


    def generate_eisporuke(self, company_id: int, dat_od: datetime.date, dat_do: datetime.date, eisporuke_last_id: int, regenerate=True):
        
        porezni_period = self._get_porezni_period(dat_od)

        if regenerate:
            self._delete_existing(porezni_period)


        domain = [
           ('company_id', '=', company_id.id),
           ('date', '>=', dat_od),
           ('date', '<=', dat_do),
           ('state', '=', 'posted'),

           '|',

            '&',
            # ulazni racuni ino usluge
            ('partner_id.property_account_payable_id.name', 'ilike', '%INO USLUGE%'),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
           
            # ili fakture
            ('move_type', 'in', ['out_invoice', 'out_refund'])

        ]
        
        

        moves = self.env['account.move'].search(domain, order="date, name")

        iter_moves = iter(list(moves.ids))
        try:
            move_id = next(iter_moves)
        except:
            move_id = 0 

        eisporuke_id = eisporuke_last_id + 1
        while move_id != 0:
            move = self.env['account.move'].browse(move_id)
            
            print(move.name, move.partner_id.name)

            fakt_iznos_sa_pdv = 0.0
            fakt_iznos_sa_pdv_interna = 0.0
            fakt_iznos_sa_pdv0_izvoz = 0.0
            fakt_iznos_sa_pdv0_ostalo = 0.0
            fakt_iznos_bez_pdv = 0.0
            fakt_iznos_bez_pdv_np = 0.0

            fakt_iznos_pdv = 0.0
            fakt_iznos_pdv_np = 0.0
            fakt_iznos_pdv_np_32 = 0.0
            fakt_iznos_pdv_np_33 = 0.0
            fakt_iznos_pdv_np_34 = 0.0

            _tip_isporuke = "01"

            if move.is_partner_ino_usluge():
                _tip_isporuke = "05"

            #move.partner_id

            # move.partner_id.country_id.code == 'BA'
            
            # krajnja potrosnja 32 - FBiH, 33 - PC, 34 - BD
            
            #partner_rejon = 1
            #if move.partner_id.state_id:
            #    if move.partner_id.state_id.code == "RS":
            #        kp = 2
            #    elif move.partner_id.state_id.code == "BD":
            #        kp = 3

            prodavac_32 = False
            prodavac_33 = False
            prodavac_34 = False
            if move.company_id.state_id:
                if move.company_id.state_id.code in ('KSA', 'ZEDO', 'TK'):
                    prodavac_32 = True
                elif move.company_id.state_id.name == "RS":
                    prodavac_33 = True
                elif move.company_id.state_id.name == "BD":
                    prodavac_33 = True
            else:
                prodavac_32 = True

            move_lines = move.line_ids.filtered(lambda ml: ml.display_type != 'payment_term')

            strani_kupac = False
            pdv_obveznik = False
            nepdv_obveznik = False

            if (not move.partner_id.country_id) or (move.partner_id.country_id and move.partner_id.country_id.code != 'BA'):
                strani_kupac = True

                if move.partner_id.vat and len(move.partner_id.vat) == 12:
                    raise UserError(f"Partner {move.partner_id.name} ima PDV broj a država nije BiH ?!")
            
            if move.partner_id.country_id.code == 'BA':
                strani_kupac = False

                if move.partner_id.vat and len(move.partner_id.vat) == 12:
                    pdv_obveznik = True
                    nepdv_obveznik = False
                else:
                    pdv_obveznik = False
                    nepdv_obveznik = True

            cnt_move_line = 0
            for move_line in move_lines:
                cnt_move_line += 1
                print(move.name, cnt_move_line)
                for tag in move_line.tax_tag_ids:
                    # partner_id
                    # tax_audit
                    # move_name
                    
                    if tag.name in ("E_BASE"):
                        if move_line.display_type != 'tax':
                            if pdv_obveznik:
                                # osnovica pdv
                                fakt_iznos_bez_pdv += -move_line.amount_currency
                            elif nepdv_obveznik:
                                fakt_iznos_bez_pdv_np += -move_line.amount_currency

                    if tag.name in ("E"):
                        # 05 - ino usluge ulazne fakture
                        if pdv_obveznik or _tip_isporuke == "05":
                            # osnovica pdv
                            fakt_iznos_pdv += -move_line.amount_currency
                        elif nepdv_obveznik:
                            fakt_iznos_pdv_np += -move_line.amount_currency
                            if prodavac_32:
                                fakt_iznos_pdv_np_32 += -move_line.amount_currency
                            elif prodavac_33:
                                fakt_iznos_pdv_np_33 += move_line.amount_currency
                            elif prodavac_34:
                                fakt_iznos_pdv_np_34 += -move_line.amount_currency

            fakt_iznos_sa_pdv = round(fakt_iznos_bez_pdv + fakt_iznos_bez_pdv_np + fakt_iznos_pdv + fakt_iznos_pdv_np, 2)

            if (round(fakt_iznos_bez_pdv, 2) == 0.0 and 
                round(fakt_iznos_bez_pdv_np, 2) == 0.0 and
                round(fakt_iznos_sa_pdv, 2) == 0.0 and
                round(fakt_iznos_sa_pdv_interna, 2) == 0.0 and
                round(fakt_iznos_sa_pdv0_izvoz, 2) == 0.0 and
                round(fakt_iznos_sa_pdv0_ostalo, 2) == 0.0 and
                round(fakt_iznos_pdv, 2) == 0.0 and
                round(fakt_iznos_pdv_np, 2) == 0.0):
                try:
                    move_id = next(iter_moves)
                except:
                    move_id = 0 
                move = self.env['account.move'].browse(move_id)
                continue

            self.env["ba.pdv.isporuke"].create({
                "eisporuke_id": eisporuke_id,
                "porezni_period": porezni_period,
                "br_fakt": move.ref if _tip_isporuke=="05" else move.name,
                "dat_fakt": move.invoice_date,

                "kup_naz": move.partner_id.display_name,
                "kup_sjediste": (move.partner_id.zip or "") + " " + (move.partner_id.city or "") + " " + (move.partner_id.street or ""),

                "kup_pdv": move.partner_id.vat,
                "kup_jib": move.partner_id.company_registry,

                "fakt_iznos_bez_pdv": round(fakt_iznos_bez_pdv, 2),
                "fakt_iznos_bez_pdv_np": round(fakt_iznos_bez_pdv_np, 2),

                "fakt_iznos_sa_pdv": round(fakt_iznos_sa_pdv, 2),

                "fakt_iznos_sa_pdv_interna": round(fakt_iznos_sa_pdv_interna, 2),
                "fakt_iznos_sa_pdv0_izvoz": round(fakt_iznos_sa_pdv0_izvoz, 2),
                "fakt_iznos_sa_pdv0_ostalo":round(fakt_iznos_sa_pdv0_ostalo, 2),
                
                "fakt_iznos_pdv": round(fakt_iznos_pdv, 2),
                "fakt_iznos_pdv_np": round(fakt_iznos_pdv_np, 2),

                "fakt_iznos_pdv_np_32": round(fakt_iznos_pdv_np_32, 2),
                "fakt_iznos_pdv_np_33": round(fakt_iznos_pdv_np_33, 2),
                "fakt_iznos_pdv_np_34": round(fakt_iznos_pdv_np_34, 2),

                "jci": "",
                "tip": _tip_isporuke,

                "move_id": move.id
            })

            eisporuke_id += 1

            try:
                move_id = next(iter_moves)
            except:
                move_id = 0 
            move = self.env['account.move'].browse(move_id)

        return porezni_period 
