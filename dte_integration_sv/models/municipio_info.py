# -*- coding: utf-8 -*-
from odoo import models, fields, api

class municipioInfo(models.Model):
    _name = "municipio.info"

    name = fields.Char(string="Nombre Municipio", required=True)
    code = fields.Char(string="Codigo Municipio", required=True)
