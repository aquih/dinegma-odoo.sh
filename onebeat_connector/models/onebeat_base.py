from odoo import models, fields, api, _


class OnebeatBase(models.AbstractModel):
    _name = "onebeat.base"
    _description = "Onebeat Base"

    def _onebeat_prepare_input_data(self):
        return {"id": self._get_onebeat_id()}

    @api.model
    def onebeat_search_in_date_range(
        self, date_from: str, date_to: str, limit=None, offset=0, company_id=None
    ):
        domain = self._onebeat_search_domain(date_from, date_to, company_id)

        return self.search(domain, limit=limit, offset=offset)

    def _onebeat_search_domain(self, date_from: str, date_to: str, company_id=None):
        domain = [("create_date", ">=", date_from), ("create_date", "<=", date_to)]

        if company_id is not None:
            domain.append(("company_id", "=", company_id))

        return domain

    def _get_onebeat_id(self) -> str:
        return str(self.id)

    def _onebeat_build_input_data(self):
        res = []

        for rec in self:
            res.append(rec._onebeat_prepare_input_data())

        return res
