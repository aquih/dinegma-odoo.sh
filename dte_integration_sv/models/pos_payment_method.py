# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    cod_forma_pago = fields.Char(string="Codigo Forma de Pago", store=True)

