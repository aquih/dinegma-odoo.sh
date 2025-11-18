# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.tools.float_utils import float_round

from odoo.exceptions import UserError, ValidationError
from ..controllers.api import ApiContext

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = ["stock.move.line", "onebeat.base"]

    def _onebeat_search_domain(self, ctx: ApiContext):
        domain = super()._onebeat_search_domain(ctx)

        # La location de tipo interna en Odoo puede mapearse a store o warehouse en OneBeat
        onebeat_types = ("store", "warehouse")

        domain += [
            ("picking_id.state", "=", "done"),
            "|",
            "|",
            # Movimientos de entrega
            "&",
            ("location_id.onebeat_type", "in", onebeat_types),
            ("location_dest_id.usage", "=", "customer"),
            # Movimientos de devolucion
            "&",
            ("location_id.usage", "=", "customer"),
            ("location_dest_id.onebeat_type", "in", onebeat_types),
            # Movimientos de recepcion
            "&",
            ("location_id.usage", "=", "supplier"),
            ("location_dest_id.onebeat_type", "in", onebeat_types),
        ]

        return domain

    def _onebeat_prepare_input_data(self):
        res = super()._onebeat_prepare_input_data()

        main_company_id = self.env["res.company"]._get_main_company()
        main_company_currency = main_company_id.currency_id

        onebeat_type = None
        origin = self.location_id.usage
        dest = self.location_dest_id.usage

        if origin == "internal" and dest == "customer":
            onebeat_type = "sale"
        elif origin == "customer" and dest == "internal":
            onebeat_type = "return"
        elif origin == "supplier" and dest == "internal":
            onebeat_type = "in"

        sale_price = 0
        currency_id = self.env["res.currency"]

        if onebeat_type == "sale":
            so_line_id = self.move_id.sale_line_id

            if so_line_id:
                sale_price = so_line_id.price_unit
                currency_id = so_line_id.currency_id
            elif self.picking_id.pos_order_id:
                # Pickings de pdv con stock en tiempo real

                po_lines_map = self.env["stock.move"]._prepare_lines_data_dict(
                    self.picking_id.pos_order_id.lines
                )

                # En caso de pos.order, buscamos la pos.order.line segun el producto
                # del stock.move.line

                if self.product_id.id in po_lines_map:
                    porder_line = po_lines_map[self.product_id.id]["order_lines"][0]
                    sale_price = porder_line.price_unit
                    currency_id = porder_line.currency_id
            elif self.picking_id.pos_session_id:
                # Picking de pdv configurado para actualizar el stock solo al cerrar la sesion
                closed_order_ids = self.picking_id.pos_session_id._get_closed_orders()

                all_lines = closed_order_ids.lines

                stockable_lines = all_lines.filtered(
                    lambda l: l.product_id.type == "consu"
                    and not float_is_zero(
                        l.qty, precision_rounding=l.product_id.uom_id.rounding
                    )
                    and l.product_id.id == self.product_id.id
                )

                po_product_lines = stockable_lines.filtered(lambda l: l.qty > 0)

                if po_product_lines:
                    sale_price = float_round(
                        (
                            sum(po_product_lines.mapped("price_unit"))
                            / len(po_product_lines)
                        ),
                        2,
                    )
                    currency_id = po_product_lines[0].currency_id

        # Conversion de moneda si es necesario
        if sale_price and main_company_currency != currency_id:
            sale_price = main_company_currency._convert(
                sale_price, currency_id, main_company_id, fields.Datetime.now()
            )

        res.update(
            {
                "sku_id": self.product_id._get_onebeat_id(),
                "quantity": self.quantity,
                "sale_price": sale_price,
                "source_location_id": self.location_id._get_onebeat_id(),
                "target_location_id": self.location_dest_id._get_onebeat_id(),
                "transaction_date": self.date.strftime("%Y-%m-%dT%H:%M:%S"),
                "type": onebeat_type,
                "currency": currency_id.name or "-",
            }
        )

        return res
