# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _


class PosOrder(models.Model):
    _inherit = "pos.order"

    es_credito_fiscal = fields.Boolean(string="Es Credito Fiscal", default=False)

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        vals["es_credito_fiscal"] = self.es_credito_fiscal
        return vals

    def _create_invoice(self, move_vals):
        invoice = super(PosOrder, self)._create_invoice(move_vals)
        if invoice.env.context.get("linked_to_pos"):
            invoice.prepare_sync_data()
        return invoice
