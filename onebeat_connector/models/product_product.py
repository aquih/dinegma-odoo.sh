# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "onebeat.base"]

    eol_date = fields.Date(string="Fecha de fin de ciclo de vida")

    def _onebeat_search_domain(self, date_from: str, date_to: str, company_id=None):
        domain = []

        if company_id is not None:
            domain.append(("company_id", "=", company_id))

        return domain

    def _onebeat_prepare_input_data(self):
        res = super()._onebeat_prepare_input_data()

        now = fields.Datetime.now()

        # Forzamos la moneda definida en la compañia principal
        main_company_id = self.env["res.company"]._get_main_company()
        currency_id = main_company_id.currency_id

        price = self.lst_price

        # standard_price es company_dependent, fuerzo a que tome el valor definido en la
        # compañia asociada a este producto (si la tiene)
        cost = self.standard_price
        if self.company_id:
            cost = self.with_company(self.company_id.id).standard_price

        # Conversion de moneda si es necesario
        if self.currency_id != currency_id:
            price = currency_id._convert(price, self.currency_id, main_company_id, now)
            cost = currency_id._convert(cost, self.currency_id, main_company_id, now)

        if self.categ_id:
            categories = "#".join(
                [c.strip() for c in self.categ_id.display_name.split("/")]
            )

            res["categories"] = categories

        # if self.image_1920:
        #     base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        #     img_url = f"{base_url}/web/image/product.product/{self.id}/image_1920"
        #     res["pictures"] = img_url

        # if self.description:
        #     res["product_description"] = self.description
        #     res["description"] = self.description

        if currency_id:
            res["cost_currency"] = currency_id.symbol
            res["price_currency"] = currency_id.symbol

        if self.eol_date:
            res["end_of_life_date"] = self.eol_date.strftime("%Y-%m-%d")

        size_attr_value = brand_attr_value = color_attr_value = None

        for attr_value_id in self.product_template_variant_value_ids:
            onebeat_attr = attr_value_id.attribute_id.onebeat_type
            if onebeat_attr == "size":
                size_attr_value = attr_value_id
            elif onebeat_attr == "brand":
                brand_attr_value = attr_value_id
            elif onebeat_attr == "color":
                color_attr_value = attr_value_id

        if size_attr_value:
            res["size"] = size_attr_value.name

        if brand_attr_value:
            res["brands"] = brand_attr_value.name

        if color_attr_value:
            res["colors"] = color_attr_value.name

        res.update(
            {
                "name": self.display_name,
                "product_name": self.product_tmpl_id.name,
                "product_id": self.product_tmpl_id.id,
                "price": price,
                "cost": cost,
                # TODO: avoid_replenishment
                "avoid_replenishment": False,
                "introduction_date": self.create_date.strftime("%Y-%m-%d"),
            }
        )

        return res
