from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from .date_util import DateUtil


ZAOKRUZENJE = 2

class BaPDVWizard(models.TransientModel):

    _name = 'ba.pdv.wizard'

    date_from = fields.Date(string="Obračun od:", required=True, default=lambda self: self._get_date_from())
    date_to = fields.Date(string="do:", required=True, default=lambda self: self._get_date_to())

    company_id = fields.Many2one(
        "res.company",
        string="Preduzeće:",
        default=lambda self: self.env.user.company_id,
    )

    enabavke_last_id = fields.Integer(string="Redni broj posljednje nabavke", compute = "_compute_last_numbers")
    eisporuke_last_id = fields.Integer(string="Redni broj posljednje isporuke", compute = "_compute_last_nubmers")

    def _get_porezni_period(self, dat_od: datetime.date):
        # 2502 - februart 2025
        return dat_od.strftime("%y%m")
    
    def _get_date_from(self):
        user_settings = self.env['res.users.settings']._find_or_create_for_user(self.env.user)._res_users_settings_format()
        if not user_settings['ba_pdv_od']:
            user_settings['ba_pdv_od'] = DateUtil.default_date_from()

        return user_settings['ba_pdv_od']
    
    def _get_last_number_nabavke(self, date_from):
        return self.env['ba.pdv.nabavke'].get_last_number(date_from)

    
    def _get_last_number_isporuke(self, date_from):
        return self.env['ba.pdv.isporuke'].get_last_number(date_from)

    @api.depends('date_from', 'date_to')
    def _compute_last_numbers(self):
        for rec in self:
            rec.enabavke_last_id = rec._get_last_number_nabavke(rec.date_from)
            rec.eisporuke_last_id = rec._get_last_number_isporuke(rec.date_from)

    def _get_date_to(self):
        user_settings = self.env['res.users.settings']._find_or_create_for_user(self.env.user)._res_users_settings_format()
        if not user_settings['ba_pdv_do']:
            user_settings['ba_pdv_do'] = DateUtil.default_date_to()
        return user_settings['ba_pdv_do']
        

    def action_generate_xlsx(self):

        user_settings = self.env['res.users.settings']._find_or_create_for_user(self.env.user)
        
        user_settings.set_res_users_settings({
             'ba_pdv_od': self.date_from,
             'ba_pdv_do': self.date_to
        })


        data = {'date_from': self.date_from,
                'date_to': self.date_to,
                'company_id': self.company_id.id,
                'enabavke_last_id': self.enabavke_last_id,
                'eisporuke_last_id': self.eisporuke_last_id,
                'model': self._name,
                'ids': self.ids,
                'docids': self.ids,
                'porezni_period': self._get_porezni_period(self.date_from),
               }


        #self.env["ir.config_parameter"].sudo().set_param(
        #    "report.default.context", '{"test_parameter": 1}'
        #)
        #report.write({"context": '{"report_name": "hernad"}'})
        #return self.env.ref('l10n_ba_pdv.pdv_xlsx_report').report_action(self, data=data)

        report = self.env.ref('l10n_ba_pdv.pdv_xlsx_report')
        _report_name = self.company_id.vat + "_" + self._get_porezni_period(self.date_from)

        return report.with_context(report_name=_report_name).report_action(self, data=data)




    def action_generate_eisporuke_csv(self):
   
        data = {'date_from': self.date_from,
                'date_to': self.date_to,
                'enabavke_last_id': self.enabavke_last_id,
                'eisporuke_last_id': self.eisporuke_last_id,
                'company_id': self.company_id.id,
                'model': self._name,
                'ids': self.ids,
                'docids': self.ids,
                'porezni_period': self._get_porezni_period(self.date_from),
               }
        
        report = self.env.ref('l10n_ba_pdv.eisporuke_csv')
        
        _report_name = self.company_id.vat + "_" + self._get_porezni_period(self.date_from) + "_2_01"
        return report.with_context(report_name=_report_name).report_action(self, data)
 

    def action_generate_enabavke_csv(self):
   
        data = {'date_from': self.date_from,
                'date_to': self.date_to,
                'enabavke_last_id': self.enabavke_last_id,
                'eisporuke_last_id': self.eisporuke_last_id,
                'company_id': self.company_id.id,
                'model': self._name,
                'ids': self.ids,
                'docids': self.ids,
                'porezni_period': self._get_porezni_period(self.date_from)
               }
        
                
        report = self.env.ref('l10n_ba_pdv.enabavke_csv')
        
        _report_name = self.company_id.vat + "_" + self._get_porezni_period(self.date_from) + "_1_01"
        return report.with_context(report_name=_report_name).report_action(self, data)

