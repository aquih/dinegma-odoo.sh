# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_studio_field_HiULv = fields.Selection(
        selection=[
            ("Hombre", "Masculino"),
            ("Mujer", "Femenino"),
            ("Unisex", "Unisex"),
            ("Niños", "Niño"),
            ("Niña", "Niña"),
        ],
        string="Genero",
    )

    x_studio_categoria = fields.Char(string="Categoria")
    x_studio_sub_cateoria = fields.Char(string="Sub categoria")
