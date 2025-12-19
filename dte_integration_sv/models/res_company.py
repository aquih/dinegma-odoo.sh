# -*- coding: utf-8 -*-
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = "res.company"


    #ENVIRONMENT CONFIGURATION
    general_stage_url = fields.Char(string="URL Test DTE", readonly=True, store=True,
                                     default="https://certificador.infile.com.sv/api/v1/certificacion/test/documento/certificar")
    general_prod_url = fields.Char(string="URL PRODUCCIÓN DTE", readonly=True, store=True,
                                     default="https://certificador.infile.com.sv/api/v1/certificacion/prod/documento/certificar")

    invalidation_stage_url = fields.Char(string="URL Test Invalidacion DTE", readonly=True, store=True,
                                     default="https://certificador.infile.com.sv/api/v1/certificacion/test/documento/invalidacion")
    invalidation_prod_url = fields.Char(string="URL PRODUCCIÓN Invalidacion DTE", readonly=True, store=True,
                                     default="https://certificador.infile.com.sv/api/v1/certificacion/prod/documento/invalidacion")


    #Credentials
    username = fields.Char(string="Usuario", store=True)
    key = fields.Char(string="Llave", store=True)
    api_token = fields.Char(string="Token", store=True)

    #Required Fields
    cod_company = fields.Char(string="Codigo Compañía", store=True)
    nrc = fields.Char(string="NRC", store=True)
    actividad_economica_id = fields.Many2one('actividad.economica', string="Actividad Económica", store=True)
    tipo_establecimiento = fields.Selection([('01','Sucursal / Agencia'),('02','Casa matriz'),('04','Bodega'),
                                             ('07','Predio y/o patio'),('20','Otro')
                                             ])
    cod_establecimiento = fields.Char(string="Codigo Establecimiento", store=True)
    departamento = fields.Selection([('01','Ahuachapán'),('02','Santa Ana'),('03','Sonsonate'),
                                     ('04', 'Chalatenango'), ('05', 'La Libertad'), ('06', 'San Salvador'),
                                     ('07', 'Cuscatlán'), ('08', 'La Paz'), ('09', 'Cabañas'),
                                     ('10', 'San Vicente'), ('11', 'Usulután'), ('12', 'San Miguel'),
                                     ('13', 'Morazán'), ('14', 'La Unión'),
                                    ])
    municipio_id = fields.Many2one('municipio.info', string="Municipio", store=True)


    tipo_documento = fields.Selection([('36','NIT'),('13','DUI'),('37','Otro'),('03','Pasaporte'),('02','Carnet de Residente'),],
                                      string="Tipo Documento", store=True)

    @api.constrains('cod_company', 'cod_punto_venta')
    def _check_exactly_four_chars(self):
        for record in self:
            # validar cod_company
            if record.cod_company and len(record.cod_company) != 4:
                raise UserError("El campo 'Código Company' debe tener exactamente 4 caracteres.")
