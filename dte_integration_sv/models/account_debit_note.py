# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountDebitNote(models.TransientModel):
    _inherit = "account.debit.note"

    def create_debit(self):
        res = super(AccountDebitNote, self).create_debit()
        account_move = self.env['account.move'].browse(res.get('res_id'))
        account_move.syncronized_with_fesv = False
        return res