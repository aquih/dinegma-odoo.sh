# -*- coding: utf-8 -*-
from datetime import datetime
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from ..controllers.api import ApiContext

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _name = "stock.quant"
    _inherit = ["stock.quant", "onebeat.base"]

    def _onebeat_search_domain(self, ctx: ApiContext):
        domain = super()._onebeat_search_domain(ctx)
        domain += [("location_id.onebeat_type", "in", ("warehouse", "store"))]

        return domain

    def _onebeat_prepare_input_data(self):
        res = {
            "location_id": self.location_id._get_onebeat_id(),
            "sku_id": self.product_id._get_onebeat_id(),
            "site_qty": max(self.available_quantity, 0),
            "transit_qty": 0,
            "source_location_id": (
                self.location_id.onebeat_src_location_id._get_onebeat_id()
                if self.location_id.onebeat_src_location_id
                else "-"
            ),
            "reserved_qty": self.reserved_quantity,
            "replenishment_lead_time": self.location_id.default_replenishment_lead_time,
            "avoid_replenishment": not self.location_id.replenish_location,
        }

        orderpoint_id = self.product_id.orderpoint_ids.filtered(
            lambda op: op.location_id == self.location_id
        )

        # Se considera q hay en stock en transito en una ubicacion para un producto, cuando hay
        # movimientos internos en espera o preparados desde una ubicacion interna
        # hacia la ubicacion que se esta evaluando.

        in_transit_move_ids = self.env["stock.move"].search(
            [
                ("picking_id.state", "in", ("confirmed", "assigned")),
                ("picking_id.picking_type_id.code", "=", "internal"),
                ("picking_id.location_id.usage", "=", "internal"),
                ("picking_id.location_dest_id.usage", "=", "internal"),
                ("picking_id.location_dest_id", "=", self.location_id.id),
                ("product_id", "=", self.product_id.id),
            ]
        )

        res["transit_qty"] = sum(in_transit_move_ids.mapped("quantity"))

        if orderpoint_id:
            res.update(
                {
                    "min_stock": orderpoint_id.product_min_qty,
                    "max_stock": orderpoint_id.product_max_qty,
                }
            )

        return res

    def _onebeat_build_input_data(self):
        res = super()._onebeat_build_input_data()

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        for obj in res:
            obj["status_date"] = now

        return res
