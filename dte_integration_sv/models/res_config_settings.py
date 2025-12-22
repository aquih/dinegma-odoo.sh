# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company
    )

    #Credenciales
    username = fields.Char(string="Username", readonly=False, related="company_id.username")
    key = fields.Char(string="Llave", readonly=False, related="company_id.key")
    api_token = fields.Char(string="Token", readonly=False, related="company_id.api_token")


    #ENVIRONMENT CONFIGURATION
    environment_bill_configuration = fields.Selection([
        ('stage', 'Stage'),
        ('production', 'Production')
    ], string="Entorno DTE",config_parameter='dte_integration_sv.environment_bill_configuration', default='stage', store=True)
    general_stage_url = fields.Char(string="URL Test DTE", readonly=True, store=True,
                                    related='company_id.general_stage_url')
    general_prod_url = fields.Char(string="URL PRODUCCIÓN DTE", readonly=True, store=True,
                                   related='company_id.general_prod_url')


    #Endpoints DTE
    auth_url = fields.Char(string="DTE Endpoint Autorización", config_parameter='dte_integration_sv.auth_url',
                           readonly=False, store=True, default="/seguridad/auth")
    unique_invoice_url = fields.Char(string="DTE Endpoint Factura Única", config_parameter='dte_integration_sv.unique_invoice_url',
                           readonly=False, store=True, default="/fesv/recepciondte")
    lot_invoice_url = fields.Char(string="DTE Endpoint Múltiples Facturas", config_parameter='dte_integration_sv.lot_invoice_url',
                           readonly=False, store=True, default="/fesv/recepcionlote/")