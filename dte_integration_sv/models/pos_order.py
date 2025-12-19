# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _create_invoice(self, move_vals):
        invoice = super(PosOrder, self)._create_invoice(move_vals)
        if invoice.env.context.get('linked_to_pos'):
            invoice.prepare_sync_data()
        return invoice