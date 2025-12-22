# -*- coding: utf-8 -*-
from odoo import models, fields, api

class actividadEconomica(models.Model):
    _name = "actividad.economica"

    name = fields.Char(string="Nombre Actividad", required=True)
    code = fields.Char(string="Codigo Actividad", required=True)
