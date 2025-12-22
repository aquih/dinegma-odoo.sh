# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _

class AccountTax(models.Model):
    _inherit = 'account.tax'

    cod_tributo = fields.Char(string="Código de Atributo", store=True)
