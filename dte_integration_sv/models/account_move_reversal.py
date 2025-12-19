# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def reverse_moves(self, is_modify=False):
        res = super(AccountMoveReversal, self).reverse_moves(is_modify)
        account_move = self.env['account.move'].browse(res.get('res_id'))
        account_move.syncronized_with_fesv = False
        return res
