import collections
import dataclasses
from datetime import datetime
import json
import traceback

from odoo import http
from odoo.http import request, HttpDispatcher
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized

import logging

_logger = logging.getLogger(__name__)


class OnebeatDispatcher(HttpDispatcher):

    routing_type = "onebeat"

    def __init__(self, request):
        super().__init__(request)

    def pre_dispatch(self, rule, args):

        if not self.request.env.user.has_group("onebeat_connector.group_onebeat_user"):
            raise Unauthorized("User does not have access to Onebeat APIs")

        super().pre_dispatch(rule, args)

    def dispatch(self, endpoint, args):
        consumed_model = endpoint.routing.get("api_model")
        url_params = dict(self.request.get_http_params(), **args)

        base_log = {
            "name": endpoint.routing["routes"][0],
            "model_name": consumed_model,
            "user_id": request.env.user.id,
            "url_params": json.dumps(url_params, indent=1),
        }

        try:
            response = super().dispatch(endpoint, args)
        except Exception as e:
            self.request._cr.rollback()
            self.request.env["onebeat.log"].create(
                {
                    **base_log,
                    "status_code": e.code if isinstance(e, HTTPException) else 500,
                    "state": "error",
                    "error_desc": str(e),
                    "error_traceback": traceback.format_exc(),
                }
            )
            self.request._cr.commit()
            raise
        else:
            self.request.env["onebeat.log"].create(
                {
                    **base_log,
                    "state": "success",
                    "status_code": 200,
                    "response": json.dumps(response.json, indent=1),
                }
            )
            return response

    def handle_error(self, exc: Exception) -> collections.abc.Callable:
        return super().handle_error(exc)


@dataclasses.dataclass
class OnebeatApiParams:
    date_from: str = ""
    date_to: str = ""
    company_id: int = None
    limit: int = None
    offset: int = 0

    @classmethod
    def from_url(cls, **kwargs):

        class_fields = [f.name for f in dataclasses.fields(OnebeatApiParams)]

        res = OnebeatApiParams(**{k: v for k, v in kwargs.items() if k in class_fields})

        for int_field in ("company_id", "limit", "offset"):
            value = getattr(res, int_field)
            if value is not None:
                try:
                    setattr(res, int_field, int(value))
                except ValueError:
                    raise BadRequest(f"Invalid parameter: {int_field}")

        return res

    def check_date_ranges(self):

        valid_format = "%Y-%m-%d"

        try:
            datetime.strptime(self.date_from, valid_format)
        except ValueError:
            raise BadRequest("Invalid parameter: date_from")

        try:
            datetime.strptime(self.date_to, valid_format)
        except ValueError:
            raise BadRequest("Invalid parameter: date_to")


class OnebeatController(http.Controller):

    def _onebeat_model_json_response(
        self, model_env, params: OnebeatApiParams, exclude_inactives=True
    ):
        """
        Construye una respuesta JSON para un modelo de Odoo específico en base a los parametros GET recibidos.
        model_env: debe ser cualquier modelo de Odoo que implemente el modelo abstracto onebeat.base
        """

        date_from = params.date_from
        date_to = params.date_to
        limit = params.limit
        offset = params.offset
        company_id = params.company_id

        records = model_env.with_context(
            active_test=exclude_inactives
        ).onebeat_search_in_date_range(date_from, date_to, limit, offset, company_id)

        dicts_list = records._onebeat_build_input_data()
        return request.make_json_response(dicts_list)

    @http.route(
        "/onebeat/locations",
        type="onebeat",
        auth="bearer",
        methods=["GET"],
        csrf=False,
        website=False,
        api_model="stock.location",
    )
    def onebeat_locations(self, **kwargs):
        params = OnebeatApiParams.from_url(**kwargs)

        StockLocation = request.env["stock.location"]
        return self._onebeat_model_json_response(StockLocation, params)

    @http.route(
        "/onebeat/catalogs",
        type="onebeat",
        auth="bearer",
        methods=["GET"],
        csrf=False,
        website=False,
        api_model="product.product",
    )
    def onebeat_catalogs(self, **kwargs):

        params = OnebeatApiParams.from_url(**kwargs)

        ProductProduct = request.env["product.product"]
        return self._onebeat_model_json_response(
            ProductProduct, params, exclude_inactives=False
        )

    @http.route(
        "/onebeat/inventories",
        type="onebeat",
        auth="bearer",
        methods=["GET"],
        csrf=False,
        website=False,
        api_model="stock.quant",
    )
    def onebeat_inventories(self, **kwargs):

        params = OnebeatApiParams.from_url(**kwargs)
        params.check_date_ranges()

        StockQuant = request.env["stock.quant"]
        return self._onebeat_model_json_response(StockQuant, params)

    @http.route(
        "/onebeat/transactions",
        type="onebeat",
        auth="bearer",
        methods=["GET"],
        csrf=False,
        website=False,
        api_model="stock.move.line",
    )
    def onebeat_transactions(self, **kwargs):

        params = OnebeatApiParams.from_url(**kwargs)
        params.check_date_ranges()

        StockMoveLine = request.env["stock.move.line"]
        return self._onebeat_model_json_response(StockMoveLine, params)
