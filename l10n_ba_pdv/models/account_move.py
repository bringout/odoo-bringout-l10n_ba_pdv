from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'


    def is_partner_ino_usluge(self):
        _konto_dobavljac = 'X'
        if self.partner_id and self.partner_id.property_account_payable_id:
            _konto_dobavljac = self.partner_id.property_account_payable_id.name.upper()
        if 'INO USLUGE' in _konto_dobavljac:
            return True
        else:
            return False

