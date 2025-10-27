# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    onebeat_type = fields.Selection(
        [("brand", "Marca"), ("size", "Talla"), ("color", "Color")],
        string="Onebeat Type",
        help="Al informar productos, determina si este atributo se informa como marca, talla o color a Onebeat",
    )
