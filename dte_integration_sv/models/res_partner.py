# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    nrc = fields.Char(string="NRC", store=True)
    departamento = fields.Selection([('01','Ahuachapán'),('02','Santa Ana'),('03','Sonsonate'),
                                     ('04', 'Chalatenango'), ('05', 'La Libertad'), ('06', 'San Salvador'),
                                     ('07', 'Cuscatlán'), ('08', 'La Paz'), ('09', 'Cabañas'),
                                     ('10', 'San Vicente'), ('11', 'Usulután'), ('12', 'San Miguel'),
                                     ('13', 'Morazán'), ('14', 'La Unión'),
                                    ])
    actividad_economica_id = fields.Many2one('actividad.economica', string="Actividad Económica", store=True)
    municipio_id = fields.Many2one('municipio.info', string="Municipio", store=True)
    tipo_documento = fields.Selection([('36','NIT'),('13','DUI'),('37','Otro'),('03','Pasaporte'),('02','Carnet de Residente'),],
                                      string="Tipo Documento", store=True)
    es_gran_contribuyente = fields.Boolean(string="Es Gran Contribuyente", default=False, store=True)