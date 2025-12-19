# -*- coding: utf-8 -*-
from odoo import models, fields, api

class UomUom(models.Model):
    _inherit = "uom.uom"

    dte_uom_code = fields.Integer(string="DTE UoM Code", store=True)