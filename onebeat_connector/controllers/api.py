import collections
import dataclasses
from datetime import datetime
import json
import traceback
import logging

from odoo import http
from odoo.http import request, HttpDispatcher
from odoo.addons.base.models.res_users import Users

from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized
import pytz


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
    date_from: datetime = None
    date_to: datetime = None
    company_id: int = None
    limit: int = None
    offset: int = 0

    has_date_ranges: bool = False

    @classmethod
    def from_url(cls, has_date_ranges=False, **kwargs):
        vals = {"has_date_ranges": has_date_ranges, "date_from": None, "date_to": None}

        for int_field in ("company_id", "limit", "offset"):
            value = kwargs.get(int_field)
            if value is not None:
                try:
                    vals[int_field] = int(value)
                except ValueError:
                    raise BadRequest(f"Invalid parameter: {int_field}")

        if has_date_ranges:
            for date_field in ("date_from", "date_to"):
                value = kwargs.get(date_field)
                try:
                    vals[date_field] = datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    raise BadRequest(f"Invalid parameter: {date_field}")

        return OnebeatApiParams(**vals)

    def localize_dates(self, user_id: Users):
        # Define la zona horaria del usuario en los rangos de fechas
        user_tz = pytz.timezone(user_id.tz)
        self.date_from = self.date_from.replace(tzinfo=user_tz)
        self.date_to = self.date_to.replace(hour=23, minute=59, second=59).replace(
            tzinfo=user_tz
        )


@dataclasses.dataclass
class ApiContext:
    user_id: Users
    params: OnebeatApiParams
    companies: list[int]
    exclude_inactives: bool = True


class OnebeatController(http.Controller):

    def _onebeat_model_json_response(
        self, model_env, params: OnebeatApiParams, exclude_inactives=True
    ):
        """
        Construye una respuesta JSON para un modelo de Odoo específico en base a los parametros GET recibidos.
        model_env: debe ser cualquier modelo de Odoo que implemente el modelo abstracto onebeat.base
        """
        ResCompany = request.env["res.company"]

        if params.company_id is not None:
            company = ResCompany.browse(params.company_id)
            if not company.is_onebeat_synchronizable:
                companies = []
            else:
                companies = [params.company_id]
        else:
            companies = ResCompany.search(
                [("is_onebeat_synchronizable", "=", True)]
            ).ids

        if not companies:
            return request.make_json_response([])

        ctx = ApiContext(
            user_id=request.env.user,
            params=params,
            companies=companies,
            exclude_inactives=exclude_inactives,
        )

        records = model_env.onebeat_search_in_date_range(ctx)

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

        params = OnebeatApiParams.from_url(has_date_ranges=True, **kwargs)
        params.localize_dates(request.env.user)

        StockMoveLine = request.env["stock.move.line"]
        return self._onebeat_model_json_response(StockMoveLine, params)
