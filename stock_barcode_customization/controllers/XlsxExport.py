# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import deque, defaultdict
from datetime import datetime
import io
import json

from werkzeug.datastructures import FileStorage

from odoo import http, _
from odoo.http import content_disposition, request
from odoo.tools import osutil
from odoo.tools.misc import xlsxwriter


class XlsxExport(http.Controller):

    @http.route("/custom-barcode/export_xlsx", type="http", auth="user", readonly=True)
    def export_xlsx(self, data):
        jdata = json.load(data) if isinstance(data, FileStorage) else json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Inventario")

        header_bold = workbook.add_format(
            {"bold": True, "pattern": 1, "bg_color": "#AAAAAA"}
        )

        location_format = workbook.add_format({
            "bold": True,
            "font_size": 12,
            "bg_color": "#D9E1F2",
        })

        Product = request.env["product.product"].sudo()

        cols = [
            "Genero",
            "Categoria",
            "Sub categoria",
            "Nombre mostrado",
            "Referencia interna",
            "Código de barras",
            "Cantidad disponible",
            "Cantidad contada",
            "Faltante",
        ]

        worksheet.set_column(0, len(cols), 40)

        genres = dict(
            request.env["product.product"]
            ._fields["x_studio_field_HiULv"]
            .get_description(request.env)["selection"]
        )

        grouped = defaultdict(list)
        for row in jdata["rows"]:
            grouped[row.get("location_name", "Sin ubicación")].append(row)

        row_index = 0

        for location, items in grouped.items():
            worksheet.write(row_index, 0, location, location_format)
            row_index += 1

            for idx, col_name in enumerate(cols):
                worksheet.write(row_index, idx, col_name, header_bold)
            row_index += 1

            for row in items:
                product_id = Product.browse(row["product_id"])
                worksheet.write(row_index, 0, genres.get(product_id.x_studio_field_HiULv, ""))
                worksheet.write(row_index, 1, product_id.x_studio_categoria or "")
                worksheet.write(row_index, 2, product_id.x_studio_sub_cateoria or "")
                worksheet.write(row_index, 3, product_id.name or "")
                worksheet.write(row_index, 4, product_id.default_code or "")
                worksheet.write(row_index, 5, product_id.barcode or "")
                worksheet.write(row_index, 6, row["quantity"])
                worksheet.write(row_index, 7, row["inventory_quantity"])
                worksheet.write(row_index, 8, (row["inventory_quantity"] - row["quantity"]))
                row_index += 1

            # row_index += 1

        workbook.close()
        xlsx_data = output.getvalue()
        filename = f"Conteo de inventario {datetime.now():%d-%m-%Y %H_%M}"

        return request.make_response(
            xlsx_data,
            headers=[
                ("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                ("Content-Disposition", content_disposition(filename + ".xlsx")),
            ],
        )
