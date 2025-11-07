# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import deque
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
        # row_plain = workbook.add_format({"pattern": 1, "bg_color": "#ffffff"})

        Product = request.env["product.product"].sudo()

        # ------- Header -------
        cols = [
            "Genero",
            "Categoria",
            "Sub categoria",
            "Nombre mostrado",
            "Referencia interna",
            "Código de barras",
            "Cantidad disponible",
            "Cantidad contada",
        ]

        for idx, col_name in enumerate(cols, start=0):
            worksheet.write(0, idx, col_name, header_bold)

        worksheet.set_column(0, len(cols), 40)

        # ------- Rows -------

        genres = dict(
            request.env["product.product"]
            ._fields["x_studio_field_HiULv"]
            .get_description(request.env)["selection"]
        )

        for idx, row in enumerate(jdata["rows"], start=1):
            product_id = Product.browse(row["product_id"])
            worksheet.write(idx, 0, genres.get(product_id.x_studio_field_HiULv, ""))
            worksheet.write(idx, 1, product_id.x_studio_categoria or "")
            worksheet.write(idx, 2, product_id.x_studio_sub_cateoria or "")
            worksheet.write(idx, 3, product_id.name or "")
            worksheet.write(idx, 4, product_id.default_code or "")
            worksheet.write(idx, 5, product_id.barcode or "")
            worksheet.write(idx, 6, row["quantity"])
            worksheet.write(idx, 7, row["inventory_quantity"])

        workbook.close()
        xlsx_data = output.getvalue()
        filename = f"Conteo de inventario {datetime.now():%d-%m-%Y %H_%M}"
        response = request.make_response(
            xlsx_data,
            headers=[
                (
                    "Content-Type",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
                ("Content-Disposition", content_disposition(filename + ".xlsx")),
            ],
        )

        return response
