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
        if invoice.reversed_entry_id:
            invoice.es_credito_fiscal = invoice.reversed_entry_id.es_credito_fiscal
        descuento_lines = invoice.invoice_line_ids.filtered(lambda l: l.price_total < 0.0)
        total_descuento = abs(sum(descuento_lines.mapped('price_total')))
        totales_lines = invoice.invoice_line_ids.filtered(lambda l: l.price_total > 0.0)
        total = sum(totales_lines.mapped('price_total'))
        porcentaje = (total_descuento/total) * 100
        for line in totales_lines:
            line.discount = porcentaje
        for line in descuento_lines:
            line.unlink()
        if invoice.env.context.get("linked_to_pos"):
            invoice.prepare_sync_data()
        return invoice
