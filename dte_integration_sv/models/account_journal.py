# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    cod_punto_venta = fields.Char(string="Codigo Punto de Venta", store=True)

    secuencia_pdv_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia PDV',
        ondelete='restrict',
        default=lambda self: self._default_secuencia_pdv(),
        )

    def _default_secuencia_pdv(self):
        return self.env['ir.sequence'].search(
            [('code', '=', 'account.journal.pdv')],
            limit=1
        )

