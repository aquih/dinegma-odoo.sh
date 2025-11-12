from datetime import date, datetime
from odoo import models, fields, api, _

from ..controllers.api import ApiContext


class OnebeatBase(models.AbstractModel):
    _name = "onebeat.base"
    _description = "Onebeat Base"

    def _onebeat_prepare_input_data(self):
        return {"id": self._get_onebeat_id()}

    @api.model
    def onebeat_search_in_date_range(self, ctx: ApiContext):
        domain = self._onebeat_search_domain(ctx)

        limit = ctx.params.limit
        offset = ctx.params.offset

        return self.with_context(active_test=ctx.exclude_inactives).search(
            domain, limit=limit, offset=offset
        )

    def _onebeat_search_domain(self, ctx: ApiContext):

        domain = []

        if ctx.params.has_date_ranges:
            domain += [
                ("create_date", ">=", ctx.params.date_from),
                ("create_date", "<=", ctx.params.date_to),
            ]

        company_id = ctx.params.company_id

        if company_id is not None:
            domain.append(("company_id", "in", [False, company_id]))

        return domain

    def _get_onebeat_id(self) -> str:
        return str(self.id)

    def _onebeat_build_input_data(self):
        res = []

        for rec in self:
            res.append(rec._onebeat_prepare_input_data())

        return res
