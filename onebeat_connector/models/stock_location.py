# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

ONEBEAT_TYPES = {
    "internal": "warehouse",
    "transit": "vwarehouse",
    "production": "plant",
    "supplier": "supplier",
    "customer": "client",
}


class StockLocation(models.Model):
    _name = "stock.location"
    _inherit = ["stock.location", "onebeat.base"]

    default_replenishment_lead_time = fields.Integer(
        string="Plazo de reposicion predeterminado"
    )

    def _onebeat_search_domain(self, date_from: str, date_to: str, company_id=None):
        domain = super()._onebeat_search_domain(date_from, date_to, company_id)
        domain.append(("usage", "in", ("internal", "customer", "supplier")))
        return domain

    def _onebeat_prepare_input_data(self):
        res = super()._onebeat_prepare_input_data()

        wh_partner_id = self.warehouse_id.partner_id

        if wh_partner_id.city:
            res["city"] = wh_partner_id.city

        if wh_partner_id.street:
            res["location_address"] = ", ".join(
                [e for e in (wh_partner_id.city, wh_partner_id.street) if e]
            )

        if wh_partner_id.state_id:
            res["region"] = ", ".join(
                [
                    e
                    for e in (
                        wh_partner_id.country_id.name,
                        wh_partner_id.state_id.name,
                    )
                    if e
                ]
            )

        res.update(
            {
                "name": self.name,
                "type": ONEBEAT_TYPES[self.usage],
                "default_replenishment_lead_time": self.default_replenishment_lead_time,
                "avoid_replenishment": not self.replenish_location,
            }
        )

        return res
