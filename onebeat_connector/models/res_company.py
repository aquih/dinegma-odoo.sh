# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    is_onebeat_synchronizable = fields.Boolean(
        string="Sincronizable con Onebeat",
        default=False,
        help="Define si los registros de esta compañia se pueden leer desde las apis",
    )
