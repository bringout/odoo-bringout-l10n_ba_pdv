# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'

    ba_pdv_od = fields.Date("PDV od")
    ba_pdv_do = fields.Date("PDV do")
