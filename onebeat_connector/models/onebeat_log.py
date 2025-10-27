# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OnebeatLog(models.Model):
    _name = "onebeat.log"
    _description = "Logs de llamadas a la api"

    _order = "request_date desc"

    name = fields.Char(string="Endpoint", readonly=True)
    state = fields.Selection(
        [("success", "Exito"), ("error", "Error")], string="Estado", readonly=True
    )

    request_date = fields.Datetime(
        string="Fecha de la peticion",
        default=lambda self: fields.Datetime.now(),
        readonly=True,
    )
    user_id = fields.Many2one("res.users", string="Usuario", readonly=True)
    model_name = fields.Char(string="Modelo consultado", readonly=True)

    response = fields.Text(string="Respuesta", readonly=True)
    status_code = fields.Integer(string="Codigo de estado", readonly=True)

    url_params = fields.Text(string="Parametros de la URL", readonly=True)

    error_desc = fields.Char(string="Descripcion del error", readonly=True)
    error_traceback = fields.Text(string="Traza del error", readonly=True)
